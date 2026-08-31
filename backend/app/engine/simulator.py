"""Simulates a full adventuring day: a sequence of encounters and rests.

This is the part a flat "XP budget" calculator can't do, because it has no
concept of a *day*. Two things carry state from one encounter to the next:

* **HP** - characters start each encounter at whatever HP they ended the
  last one with, unless a rest happened in between. A long rest fully
  restores HP; a short rest leaves HP as-is unless the day plan records
  Hit Dice/healing actually spent during it (``rest.heals``), in which case
  that amount is added back, capped at max HP.
* **Resource pools** - spell slots, Rage, Ki, etc. Long rests reset
  everything; short rests only reset resources flagged ``regen: "short"``
  (this is why a Warlock's pact slots recovering on a short rest, versus a
  Wizard's slots needing a long rest, is a real planning difference and not
  just flavor text).

For each encounter the engine computes two independent verdicts:

1. The classic 2014 DMG XP-budget difficulty label (per-character
   thresholds with the monster-count multiplier).
2. A "rounds to kill" race: the party's *effective* damage output (after
   monster resistances) against the monster pool's HP, versus a fixed pool
   of monster damage output for the round (monsters only get to act once
   each, so this total doesn't grow with party size), split across
   characters weighted by their own individualized vulnerability (their own
   AC, their own per-ability save bonuses, their own damage resistances).
   This is where action economy, resistances, save proficiencies, and
   resource depletion from earlier fights actually show up in the number,
   instead of being invisible the way they are in a pure XP comparison.

When a resource represents a *known spell* (see :mod:`app.engine.spells`),
spending it computes real spell damage - an attack roll or a saving throw
against this encounter's actual monsters - rather than a flat average.

Every resource also has a ``timing`` (default ``"burst"``):

* ``"burst"`` - a one-time lump of damage from a single use (a spell slot,
  Ki, Superiority Dice, Divine Smite, ...), averaged across the encounter's
  assumed rounds. Multiple burst resources can be spent in the same
  encounter independently of each other - the engine works at per-encounter
  resource budgets, not per-turn action economy, so "a spell slot and a
  Metamagic point in the same turn" was never actually a conflict here.

  A burst can additionally be flagged ``displaces_at_will``: casting a
  leveled spell uses the same action a cantrip/weapon swing would have, so
  it replaces one round's worth of at-will damage rather than stacking on
  top of a full turn of it - spending N such charges in a ``rounds_assumed``
  fight scales the at-will contribution down to ``(rounds_assumed - N) /
  rounds_assumed`` of normal. Spell slots default to this; Divine Smite and
  Superiority Dice don't, since they trigger on an attack the character is
  already making rather than costing their action.
* ``"ongoing"`` - Rage: activated once, then applies to *every* attack for
  the rest of the fight. Folded into the character's flat damage bonus
  before the at-will profile is computed, so it scales with however many
  attacks the character actually makes instead of being diluted by the
  number of rounds assumed.

Multi-monster-group encounters (e.g. a boss plus adds with different
resistances) are handled by blending: the party's damage is blended across
monster groups weighted by each group's share of total monster HP, and the
incoming damage-type mix is blended weighted by each group's share of total
monster DPR. This is a documented approximation (see the project README) -
a genuinely optimal party would focus fire on the least-resistant target.
"""
from __future__ import annotations

from typing import Mapping

from .character import compute_character_profile, resolve_resource_type, save_bonus_for, spell_attack_bonus_for, spell_save_dc_for
from .classes_data import ABILITIES
from .damage_types import combined_multiplier
from .monster import compute_monster_profile
from .spells import dice_avg_for_slot, expected_leveled_spell_damage, merge_spell_registry, targets_hit
from .xp_budget import difficulty_label, party_adjusted_multiplier


def _avg_party_level(party: list[dict]) -> int:
    if not party:
        return 1
    return round(sum(c["level"] for c in party) / len(party))


def simulate_day(
    party: list[dict], bestiary: list[dict], items: list[dict], *,
    custom_spells: list[dict] | None = None,
    starting_hp: Mapping[str, float] | None = None,
    starting_resources: Mapping[str, Mapping[str, float]] | None = None,
) -> dict:
    """Run the whole day and return ``{"snapshots": [...]}``, one entry per
    item in ``items`` (``None`` for rests, a result dict for encounters).

    ``custom_spells`` is a campaign's Spell Library - user-authored spells
    that work exactly like the built-in list once merged in.

    ``starting_hp`` / ``starting_resources`` let a day start with the party
    already worn down (e.g. picking up mid-adventure) instead of assuming
    everyone begins at full - keyed by character id, sparse (only characters
    that aren't starting fresh need an entry).

    Each encounter item may also carry an ``"hp_overrides"`` dict
    (``{char_id: actual_hp_left}``): whatever the engine predicts a
    character's HP will be after that fight is just a prediction shown for
    editing - if the real table session went differently, the override is
    what actually carries forward into the next encounter or rest.
    """
    registry = merge_spell_registry(custom_spells)
    starting_hp = starting_hp or {}
    starting_resources = starting_resources or {}

    bestiary_by_id = {m["id"]: m for m in bestiary}
    hp = {c["id"]: starting_hp.get(c["id"], c["max_hp"]) for c in party}
    resources = {
        c["id"]: {r["name"]: starting_resources.get(c["id"], {}).get(r["name"], r["max"]) for r in c["resources"]}
        for c in party
    }

    snapshots: list[dict | None] = []
    avg_level = _avg_party_level(party)

    for encounter_index, item in enumerate(items):
        if item["type"] == "rest":
            heals = item.get("heals", {})
            for c in party:
                if item["rest_type"] == "long":
                    hp[c["id"]] = c["max_hp"]
                    for r in c["resources"]:
                        resources[c["id"]][r["name"]] = r["max"]
                else:
                    for r in c["resources"]:
                        if r["regen"] == "short":
                            resources[c["id"]][r["name"]] = r["max"]
                    healed = heals.get(c["id"], 0)
                    if healed:
                        hp[c["id"]] = min(c["max_hp"], hp[c["id"]] + healed)
            snapshots.append(None)
            continue

        snapshots.append(_simulate_encounter(item, party, bestiary_by_id, hp, resources, avg_level, encounter_index, registry))

    return {"snapshots": snapshots}


def _resource_nova_damage(
    ch: Mapping, resource: Mapping, used: int, avg_monster_ac: float,
    avg_monster_save_bonus_by_ability: Mapping[str, float], registry: dict, monster_count: int,
    legendary_resistance_coverage: float = 0.0,
) -> float:
    """Expected total damage from spending ``used`` charges of one resource,
    using real spell mechanics when the resource has an assigned spell -
    checking the specific saving-throw ability that spell actually calls
    for (a Fireball checks Dexterity; it doesn't care about a monster's
    Wisdom save), and multiplying by however many targets a genuine AoE
    spell should be expected to catch in this specific encounter.

    ``legendary_resistance_coverage`` (0-1) is what fraction of this
    encounter's save-based spell casts a legendary monster is expected to
    auto-succeed against, per the real 5e rule of converting a limited
    number of failed saves into successes - see :func:`_simulate_encounter`
    for how it's computed. Only save-mode spells are affected; a spell
    attack roll isn't a saving throw and Legendary Resistance has no say
    over it.
    """
    spell_id = resource.get("spell_id")
    if spell_id and spell_id in registry:
        slot_level = resource.get("slot_level", 1)
        spell = registry[spell_id]
        spell_atk = spell_attack_bonus_for(ch)
        spell_dc = spell_save_dc_for(ch)
        save_bonus = avg_monster_save_bonus_by_ability.get(spell.get("save_ability", "dex"), 0) if spell["mode"] == "save" else 0
        per_cast = expected_leveled_spell_damage(
            spell, slot_level, attack_bonus=spell_atk, target_ac=avg_monster_ac,
            save_dc=spell_dc, target_save_bonus=save_bonus,
        )
        if spell["mode"] == "save" and legendary_resistance_coverage > 0:
            guaranteed_success_dmg = dice_avg_for_slot(spell, slot_level) * 0.5 if spell.get("half_on_save") else 0.0
            per_cast = per_cast * (1 - legendary_resistance_coverage) + guaranteed_success_dmg * legendary_resistance_coverage
        per_cast *= targets_hit(spell, monster_count)
        return used * per_cast
    return used * resource["avg_value"]


def _simulate_encounter(
    item: Mapping, party: list[dict], bestiary_by_id: dict, hp: dict, resources: dict,
    avg_level: int, encounter_index: int, registry: dict,
) -> dict:
    resources_before = {c["id"]: dict(resources[c["id"]]) for c in party}
    hp_before = dict(hp)

    groups = [
        {"monster": bestiary_by_id[g["bestiary_id"]], "count": g["count"], "bestiary_id": g["bestiary_id"]}
        for g in item.get("monsters", []) if g["bestiary_id"] in bestiary_by_id
    ]
    total_monster_hp = sum(g["monster"]["max_hp"] * g["count"] for g in groups)
    total_xp = sum(g["monster"].get("xp", 0) * g["count"] for g in groups)
    monster_count = sum(g["count"] for g in groups)
    avg_monster_ac = (
        sum(g["monster"]["ac"] * g["count"] for g in groups) / monster_count if monster_count else 13
    )
    # Blended per-ability monster save bonus (count-weighted across groups),
    # falling back to a flat legacy "save_bonus" field for older data.
    avg_monster_save_bonus_by_ability = {
        ability: (
            sum(g["monster"].get("save_bonuses", {}).get(ability, g["monster"].get("save_bonus", 2)) * g["count"] for g in groups)
            / monster_count if monster_count else 2
        )
        for ability in ABILITIES
    }

    effective_xp_for_label = total_xp * party_adjusted_multiplier(monster_count, len(party))
    label = difficulty_label(effective_xp_for_label, avg_level, len(party))

    avg_party_ac = sum(c["ac"] for c in party) / len(party) if party else 15
    avg_party_save_bonus_by_ability = {
        ability: (sum(save_bonus_for(c, ability) for c in party) / len(party) if party else 10)
        for ability in ABILITIES
    }
    monster_uses = item.get("monster_uses", {})

    # --- resolve resource spend exactly once ---
    # How many charges of each resource get spent is a fixed input (item.spends)
    # that doesn't depend on how long the fight is assumed to last, so this
    # happens up front and mutates `resources` exactly once - everything below
    # this point is a pure (non-mutating) computation that gets re-run a few
    # times against different candidate round counts to converge on a
    # self-consistent answer, and must NOT touch `resources` again.
    spend_map_all = item.get("spends", {})
    per_char_spend: dict[str, dict] = {}
    for c in party:
        spend_map = spend_map_all.get(c["id"], {})
        ongoing_bonus = 0.0
        nova_spends: list[tuple[dict, int]] = []
        displacing_uses = 0
        for r in c["resources"]:
            want = spend_map.get(r["name"], 0)
            have = resources[c["id"]].get(r["name"], 0)
            used = min(want, have)
            resources[c["id"]][r["name"]] = have - used
            if used <= 0:
                continue
            if r.get("timing", "burst") == "ongoing":
                ongoing_bonus += used * r["avg_value"]
            else:
                nova_spends.append((r, used))
                if r.get("displaces_at_will"):
                    displacing_uses += used
        per_char_spend[c["id"]] = {"ongoing_bonus": ongoing_bonus, "nova_spends": nova_spends, "displacing_uses": displacing_uses}

    # Legendary Resistance converts a limited number of failed saves into
    # automatic successes - a real, damage-relevant effect, not just a
    # reference number. Both quantities here are fixed regardless of how
    # many rounds the fight is assumed to take, so this is computed once,
    # not inside compute_rates(): total save-based spell casts against
    # monsters this encounter (summed across every character's spend,
    # since the party doesn't announce in advance which specific monster
    # a cast targets - everything's blended, same as the rest of this
    # engine), and how many of those a legendary monster can just shrug off.
    total_save_casts = 0
    for info in per_char_spend.values():
        for r, used in info["nova_spends"]:
            spell = registry.get(r.get("spell_id"))
            if spell and spell.get("mode") == "save":
                total_save_casts += used
    total_legendary_resistances = sum(
        g["monster"].get("legendary_resistances", 0) * g["count"] for g in groups if g["monster"].get("is_legendary")
    )
    legendary_resistance_coverage = (
        min(1.0, total_legendary_resistances / total_save_casts) if total_save_casts > 0 else 0.0
    )

    hp_shares = [
        (g["monster"], (g["monster"]["max_hp"] * g["count"]) / total_monster_hp if total_monster_hp else 1 / max(1, len(groups)))
        for g in groups
    ]

    def blended_multiplier(dtype: str, magical: bool) -> float:
        return sum(share * combined_multiplier(monster, dtype, magical) for monster, share in hp_shares)

    def compute_rates(rounds_guess: float):
        """Pure (non-mutating) computation of everything that depends on how
        many rounds the fight is assumed to last, for a given candidate
        value. Resources aren't all the same shape - see the ``timing`` docs
        above the module - and both the party's spell-slot displacement and
        a monster's own attack displacement scale with this same candidate,
        which is why it has to be solved for rather than guessed once.
        """
        # --- monster -> party ---
        # Monsters only get to act once each per round, so the *total*
        # damage they can output in a round is a single fixed pool (computed
        # against an average party AC/save, since monsters don't know in
        # advance who they'll hit) - it must NOT grow just because the party
        # has more members. That fixed pool is then split across the party,
        # weighted by each character's own individual vulnerability (their
        # own real AC and saves), so a character with worse defenses takes a
        # bigger slice without the party's total incoming damage changing
        # based on party size.
        total_monster_dpr = 0.0
        for g in groups:
            special_uses = monster_uses.get(g["bestiary_id"], {})
            prof = compute_monster_profile(
                g["monster"], avg_party_ac, avg_party_save_bonus_by_ability, registry, len(party),
                special_uses, rounds_guess,
            )
            total_monster_dpr += g["count"] * prof["total_dpr"]

        vulnerability_weight: dict[str, float] = {}
        for c in party:
            save_bonuses_for_c = {ability: save_bonus_for(c, ability) for ability in ABILITIES}
            weight = 0.0
            for g in groups:
                special_uses = monster_uses.get(g["bestiary_id"], {})
                prof = compute_monster_profile(
                    g["monster"], c["ac"], save_bonuses_for_c, registry, len(party), special_uses, rounds_guess,
                )
                weight += g["count"] * sum(
                    comp["amount"] * combined_multiplier(c, comp["type"], comp["magical"]) for comp in prof["components"]
                )
            vulnerability_weight[c["id"]] = weight
        weight_sum = sum(vulnerability_weight.values())

        per_character_incoming: dict[str, float] = {}
        for c in party:
            share = vulnerability_weight[c["id"]] / weight_sum if weight_sum > 0 else (1 / len(party) if party else 0)
            per_character_incoming[c["id"]] = total_monster_dpr * share

        # --- party -> monsters ---
        party_dpr_total = 0.0
        for c in party:
            info = per_char_spend[c["id"]]
            buffed_c = {**c, "flat_damage_bonus": c["flat_damage_bonus"] + info["ongoing_bonus"]} if info["ongoing_bonus"] else c
            profile = compute_character_profile(buffed_c, avg_monster_ac, avg_monster_save_bonus_by_ability, registry)
            at_will_effective = sum(
                comp["amount"] * blended_multiplier(comp["type"], comp["magical"]) for comp in profile["components"]
            )

            nova_effective = 0.0
            for r, used in info["nova_spends"]:
                raw_amount = _resource_nova_damage(
                    c, r, used, avg_monster_ac, avg_monster_save_bonus_by_ability, registry, monster_count,
                    legendary_resistance_coverage,
                )
                dtype, magical = resolve_resource_type(c, r, registry)
                nova_effective += raw_amount * blended_multiplier(dtype, magical)

            at_will_rounds = max(0, rounds_guess - info["displacing_uses"])
            party_dpr_total += at_will_effective * at_will_rounds / rounds_guess + nova_effective / rounds_guess

        return total_monster_dpr, per_character_incoming, party_dpr_total

    # --- solve for a self-consistent fight length instead of trusting a
    # guessed default: both sides' resource math above scales with however
    # many rounds the fight is assumed to take, and the actual answer
    # (whichever happens first - the monsters die, or a PC drops) is only
    # known after computing it. A handful of iterations converges quickly:
    # each pass feeds the previous pass's answer back in as the next guess.
    rounds_guess = 3.0
    for _ in range(6):
        total_monster_dpr, per_character_incoming, party_dpr_total = compute_rates(rounds_guess)
        rounds_to_kill_monsters = total_monster_hp / party_dpr_total if party_dpr_total > 0 else 999.0
        rounds_to_drop_pc = 999.0
        for c in party:
            inc = per_character_incoming[c["id"]]
            if inc > 0:
                rounds_to_drop_pc = min(rounds_to_drop_pc, hp[c["id"]] / inc)
        next_guess = max(0.1, min(min(rounds_to_kill_monsters, rounds_to_drop_pc), 50.0))
        if abs(next_guess - rounds_guess) < 0.01:
            rounds_guess = next_guess
            break
        rounds_guess = next_guess

    warnings = []
    for c in party:
        displacing_uses = per_char_spend[c["id"]]["displacing_uses"]
        if displacing_uses > rounds_guess:
            warnings.append(
                f"{c['name']} spends more spell-slot casts ({displacing_uses}) than this fight is expected to last "
                f"(~{rounds_guess:.1f} rounds) - that's more spells than they realistically have turns to cast."
            )
    if party and monster_count / len(party) >= 2:
        warnings.append(f"{monster_count} monsters vs {len(party)} PCs. Action economy favors the monsters regardless of the XP total.")
    if any(g["monster"].get("is_legendary") for g in groups):
        warnings.append("Legendary actions are firing between PC turns. That damage is already folded into the monster DPR above.")
    total_nova_available = sum(
        sum(resources_before[c["id"]].get(r["name"], 0) * r["avg_value"] for r in c["resources"]) for c in party
    )
    if total_nova_available < 30 and encounter_index > 0:
        warnings.append("Party is entering this fight with most nova resources already spent.")
    if rounds_to_drop_pc <= 2:
        warnings.append("A character could realistically go down in 2 rounds or less. Expect deaths without smart play.")

    damage_mix_note = None
    if any(g["monster"].get("resistances") or g["monster"].get("vulnerabilities") or g["monster"].get("immunities") for g in groups):
        damage_mix_note = "Party damage is already discounted/boosted for these monsters' resistances, vulnerabilities and immunities."

    rounds_elapsed = max(0.0, rounds_guess)
    predicted_hp_after = {
        c["id"]: max(0, round(hp[c["id"]] - per_character_incoming[c["id"]] * rounds_elapsed)) for c in party
    }
    # The predicted value is only ever a starting point: if the day plan
    # carries a manual override for this encounter (the table played it out
    # differently than expected), that's what actually carries forward.
    hp_overrides = item.get("hp_overrides", {})
    for c in party:
        hp[c["id"]] = hp_overrides[c["id"]] if c["id"] in hp_overrides else predicted_hp_after[c["id"]]

    return {
        "total_monster_hp": total_monster_hp, "monster_dpr_total": total_monster_dpr, "total_xp": total_xp,
        "avg_monster_ac": avg_monster_ac, "avg_party_ac": avg_party_ac,
        "party_dpr_total": party_dpr_total, "rounds_to_kill_monsters": rounds_to_kill_monsters,
        "rounds_to_drop_pc": rounds_to_drop_pc, "rounds_assumed": rounds_guess,
        "label": label, "budget": label["budget"],
        "resources_before": resources_before, "warnings": warnings,
        "hp_before": hp_before, "predicted_hp_after": predicted_hp_after, "hp_after": dict(hp),
        "damage_mix_note": damage_mix_note,
    }
