"""Turns a character's build into a list of typed damage components.

A character is a plain dict (see ``docs/schema.md``). This module never
mutates its input and never touches the database - it's pure game math,
which is what makes it easy to unit test in isolation from Flask or
SQLAlchemy.
"""
from __future__ import annotations

from typing import Mapping

from .classes_data import (
    CASTING_ABILITY,
    FEATS,
    SAVE_PROFICIENCIES,
    SUBCLASS_DAMAGE_BONUS,
    ability_mod,
    eldritch_blast_beams,
    generic_cantrip_avg,
    prof_bonus,
)
from .dice_math import die_avg, expected_attack_damage, hit_chance
from .spells import SPELLS, expected_cantrip_damage


def save_bonus_for(ch: Mapping, ability: str) -> float:
    """A character's saving-throw bonus for one specific ability (str/dex/
    con/int/wis/cha), computed from their actual ability score plus
    proficiency bonus if they're proficient in that save - not a single
    flat number applied to every save regardless of which one is being
    tested."""
    score = ch.get("ability_scores", {}).get(ability, 10)
    mod = ability_mod(score)
    profs = ch.get("saving_throw_proficiencies")
    if profs is None:
        profs = SAVE_PROFICIENCIES.get(ch.get("cls", ""), [])
    prof = prof_bonus(ch["level"]) if ability in profs else 0
    return mod + prof


def spell_attack_bonus_for(ch: Mapping) -> float:
    """Default spell attack bonus, from the class's casting ability - only
    used when the character doesn't have an explicit override set."""
    override = ch.get("spell_attack_bonus")
    if override is not None:
        return override
    casting_ability = CASTING_ABILITY.get(ch.get("cls", ""), "int")
    casting_mod = ability_mod(ch.get("ability_scores", {}).get(casting_ability, 10))
    return casting_mod + prof_bonus(ch["level"])


def spell_save_dc_for(ch: Mapping) -> float:
    """Default spell save DC, from the class's casting ability - only used
    when the character doesn't have an explicit override set."""
    override = ch.get("spell_save_dc")
    if override is not None:
        return override
    casting_ability = CASTING_ABILITY.get(ch.get("cls", ""), "int")
    casting_mod = ability_mod(ch.get("ability_scores", {}).get(casting_ability, 10))
    return 8 + casting_mod + prof_bonus(ch["level"])


def compute_character_profile(
    ch: Mapping, target_ac: float, target_save_bonuses: Mapping[str, float] | None = None,
    spells_registry: dict | None = None,
) -> dict:
    """Return ``{"components": [...], "hit_pct": float, "to_hit_mod": float}``.

    ``components`` is the list of typed damage sources for one turn's
    at-will routine: weapon attacks, rider dice (Sneak Attack, Hunter's
    Mark, Hex), a cantrip if the character is a caster in cantrip mode, bonus
    attacks from feats like Polearm Master, and a flat subclass signature-
    feature bonus where one is calibrated (see ``classes_data.SUBCLASS_DAMAGE_BONUS``).

    Resource/nova spend (spell slots, Rage charges, Ki, ...) is intentionally
    *not* included here - how much of a resource gets spent is a per-encounter
    decision, not a property of the build. See :mod:`app.engine.simulator`.

    ``target_save_bonuses`` (a dict like ``{"dex": 3, "wis": 1, ...}``) is
    only consulted for a save-based cantrip (Sacred Flame, Toll the Dead,
    Vicious Mockery) - everything else in this function is either an attack
    roll against ``target_ac`` or an automatic hit.

    ``spells_registry`` defaults to the built-in spell list; pass a merged
    dict (see :func:`app.engine.spells.merge_spell_registry`) to also
    consider a campaign's custom Spell Library entries.
    """
    target_save_bonuses = target_save_bonuses or {}
    pb = prof_bonus(ch["level"])
    to_hit_mod = ch["attack_ability_mod"] + pb + ch.get("magic_weapon_bonus", 0)
    flat_dmg = ch["flat_damage_bonus"]
    feats = ch.get("feats", {})

    if feats.get("gwm"):
        to_hit_mod += FEATS["gwm"]["to_hit"]
        flat_dmg += FEATS["gwm"]["dmg"]
    if feats.get("ss"):
        to_hit_mod += FEATS["ss"]["to_hit"]
        flat_dmg += FEATS["ss"]["dmg"]
    if feats.get("dueling_style"):
        flat_dmg += FEATS["dueling_style"]["flat_dmg"]
    if feats.get("archery_style"):
        to_hit_mod += FEATS["archery_style"]["to_hit"]
    dmg_mult = FEATS["savage"]["dmg_mult"] if feats.get("savage") else 1.0

    components: list[dict] = []
    subclass_bonus = SUBCLASS_DAMAGE_BONUS.get(ch["cls"], {}).get(ch.get("subclass", ""), 0)

    if ch.get("is_caster") and ch.get("use_cantrip"):
        hit_pct = hit_chance(to_hit_mod, target_ac)
        spell_atk = spell_attack_bonus_for(ch)
        spell_dc = spell_save_dc_for(ch)
        registry = spells_registry if spells_registry is not None else SPELLS
        cantrip = registry.get(ch.get("cantrip_id"))
        if cantrip:
            save_bonus = target_save_bonuses.get(cantrip.get("save_ability", "dex"), 0) if cantrip["mode"] == "save" else 0
            amount = expected_cantrip_damage(
                cantrip, ch["level"], attack_bonus=spell_atk, target_ac=target_ac,
                save_dc=spell_dc, target_save_bonus=save_bonus,
            ) * dmg_mult
            components.append({"source": f"cantrip ({cantrip['name']})", "type": cantrip["damage_type"],
                                "magical": True, "amount": amount})
        else:
            beams = eldritch_blast_beams(ch["level"]) if ch["cls"] == "Warlock" else 1
            per_beam_avg = ch.get("cantrip_die_override") or generic_cantrip_avg(ch["level"])
            amount = beams * expected_attack_damage(to_hit_mod, target_ac, per_beam_avg, flat_dmg) * dmg_mult
            components.append({"source": "cantrip (generic)", "type": ch["weapon_damage_type"],
                                "magical": True, "amount": amount})
        if subclass_bonus:
            components.append({"source": f"{ch.get('subclass', 'subclass')} feature", "type": ch["weapon_damage_type"],
                                "magical": True, "amount": subclass_bonus})
        return {"components": components, "hit_pct": hit_pct, "to_hit_mod": to_hit_mod}

    hit_pct = hit_chance(to_hit_mod, target_ac)
    w_die = die_avg(ch["weapon_die_count"], ch["weapon_die_sides"])
    main = ch["num_attacks"] * expected_attack_damage(to_hit_mod, target_ac, w_die, flat_dmg) * dmg_mult
    components.append({
        "source": "weapon", "type": ch["weapon_damage_type"],
        "magical": bool(ch.get("attack_is_magical")), "amount": main,
    })

    rider_die = die_avg(ch.get("rider_dice_count", 0), ch.get("rider_die_sides", 6))
    if rider_die > 0:
        components.append({
            "source": "rider", "type": ch.get("rider_damage_type", ch["weapon_damage_type"]),
            "magical": bool(ch.get("attack_is_magical")), "amount": hit_pct * rider_die * dmg_mult,
        })

    if feats.get("pam"):
        d = die_avg(1, FEATS["pam"]["extra_die"])
        components.append({
            "source": "Polearm Master bonus attack", "type": ch["weapon_damage_type"],
            "magical": bool(ch.get("attack_is_magical")), "amount": expected_attack_damage(to_hit_mod, target_ac, d, flat_dmg),
        })
    if feats.get("cbe"):
        d = die_avg(1, FEATS["cbe"]["extra_die"])
        components.append({
            "source": "Crossbow Expert bonus attack", "type": ch["weapon_damage_type"],
            "magical": bool(ch.get("attack_is_magical")), "amount": expected_attack_damage(to_hit_mod, target_ac, d, flat_dmg),
        })

    if subclass_bonus:
        components.append({
            "source": f"{ch.get('subclass', 'subclass')} feature", "type": ch["weapon_damage_type"],
            "magical": bool(ch.get("attack_is_magical")), "amount": subclass_bonus,
        })

    return {"components": components, "hit_pct": hit_pct, "to_hit_mod": to_hit_mod}


def profile_total(components: list[dict]) -> float:
    return sum(c["amount"] for c in components)


def resolve_resource_type(ch: Mapping, resource: Mapping, spells_registry: dict | None = None) -> tuple[str, bool]:
    """Determine the damage type/magical-ness used for resistance purposes.

    Priority: an assigned real spell's own damage type (spells are always
    magical) > the ``"weapon"`` sentinel, which inherits the character's own
    weapon type/magical-ness (e.g. Rage adds flat damage on top of a weapon
    hit rather than being its own attack) > an explicit type on the resource.
    """
    spell_id = resource.get("spell_id")
    if spell_id:
        from .spells import SPELLS
        registry = spells_registry if spells_registry is not None else SPELLS
        spell = registry.get(spell_id)
        if spell:
            return spell["damage_type"], True
    if resource.get("damage_type") == "weapon":
        return ch["weapon_damage_type"], bool(ch.get("attack_is_magical"))
    return resource.get("damage_type", "force"), bool(resource.get("magical", True))
