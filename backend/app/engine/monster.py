"""Monster damage profile computation.

Monsters are built the same way characters are: a list of attacks (each
with its own to-hit bonus, dice, and damage type), optional save-based
attacks for breath weapons/AoEs, optional innate spellcasting (drawing on
the same spell list characters use), and optional legendary actions for
bosses. Nothing here is pulled from a monster manual - the ``CR_SEED``
table only exists to prefill plausible starting numbers for a brand-new
stat block.
"""
from __future__ import annotations

from typing import Mapping

from .classes_data import ABILITIES
from .dice_math import die_avg, expected_attack_damage, hit_chance
from .spells import SPELLS, expected_leveled_spell_damage, targets_hit

# Optional convenience seed, NOT a source of truth. AC/HP/attack/DPR midpoints
# roughly track the classic "Monster Statistics by Challenge Rating" shape,
# reduced to a single ballpark attack routine the user immediately edits.
CR_SEED: dict[str, dict] = {
    "0": {"xp": 10, "ac": 13, "hp": 6, "atk": 3, "dpr": 1},
    "1/8": {"xp": 25, "ac": 13, "hp": 21, "atk": 3, "dpr": 3},
    "1/4": {"xp": 50, "ac": 13, "hp": 43, "atk": 3, "dpr": 5},
    "1/2": {"xp": 100, "ac": 13, "hp": 60, "atk": 3, "dpr": 7},
    "1": {"xp": 200, "ac": 13, "hp": 78, "atk": 3, "dpr": 12},
    "2": {"xp": 450, "ac": 13, "hp": 93, "atk": 3, "dpr": 18},
    "3": {"xp": 700, "ac": 13, "hp": 108, "atk": 4, "dpr": 24},
    "4": {"xp": 1100, "ac": 14, "hp": 123, "atk": 5, "dpr": 30},
    "5": {"xp": 1800, "ac": 15, "hp": 138, "atk": 6, "dpr": 36},
    "6": {"xp": 2300, "ac": 15, "hp": 153, "atk": 6, "dpr": 42},
    "7": {"xp": 2900, "ac": 15, "hp": 168, "atk": 6, "dpr": 48},
    "8": {"xp": 3900, "ac": 16, "hp": 183, "atk": 7, "dpr": 54},
    "9": {"xp": 5000, "ac": 16, "hp": 198, "atk": 7, "dpr": 60},
    "10": {"xp": 5900, "ac": 17, "hp": 213, "atk": 7, "dpr": 66},
    "11": {"xp": 7200, "ac": 17, "hp": 228, "atk": 8, "dpr": 72},
    "12": {"xp": 8400, "ac": 17, "hp": 243, "atk": 8, "dpr": 78},
    "13": {"xp": 10000, "ac": 18, "hp": 258, "atk": 8, "dpr": 84},
    "14": {"xp": 11500, "ac": 18, "hp": 273, "atk": 8, "dpr": 90},
    "15": {"xp": 13000, "ac": 18, "hp": 288, "atk": 8, "dpr": 96},
    "16": {"xp": 15000, "ac": 18, "hp": 303, "atk": 9, "dpr": 102},
    "17": {"xp": 18000, "ac": 18, "hp": 318, "atk": 10, "dpr": 108},
    "18": {"xp": 20000, "ac": 19, "hp": 333, "atk": 10, "dpr": 114},
    "19": {"xp": 22000, "ac": 19, "hp": 348, "atk": 10, "dpr": 120},
    "20": {"xp": 25000, "ac": 19, "hp": 378, "atk": 10, "dpr": 132},
    "21": {"xp": 33000, "ac": 19, "hp": 423, "atk": 11, "dpr": 150},
    "22": {"xp": 41000, "ac": 19, "hp": 468, "atk": 11, "dpr": 168},
    "23": {"xp": 50000, "ac": 19, "hp": 513, "atk": 11, "dpr": 186},
    "24": {"xp": 62000, "ac": 19, "hp": 558, "atk": 12, "dpr": 204},
}
CR_ORDER = list(CR_SEED.keys())


def seed_monster_from_cr(cr: str) -> dict:
    """A plausible one-attack starting stat block for the given CR - a
    starting point to hand-edit, not a canonical lookup."""
    t = CR_SEED[cr]
    flat_bonus = max(0, round(t["dpr"] / 2 - die_avg(2, 6)))
    return {
        "ac": t["ac"], "max_hp": t["hp"], "xp": t["xp"],
        "save_bonuses": {a: t["atk"] for a in ABILITIES},
        "attacks": [{
            "name": "Attack", "count": 2, "to_hit": t["atk"],
            "die_count": 2, "die_sides": 6, "flat_bonus": flat_bonus,
            "damage_type": "slashing", "magical": False,
        }],
    }


def compute_monster_profile(
    monster: Mapping, target_ac: float, target_save_bonuses: Mapping[str, float], spells_registry: dict | None = None,
    party_size: int = 1, special_uses: Mapping[str, float] | None = None, rounds_assumed: int = 1,
) -> dict:
    """Return ``{"components": [...], "total_dpr": float}`` for one monster's
    expected damage output *per round*, against a given target AC and a dict
    of the target party's average save bonus per ability
    (``{"str": 1, "dex": 3, ...}``) - each save-based attack or spell checks
    against whichever ability it actually calls for, not one blended number.

    ``spells_registry`` defaults to the built-in spell list; pass a merged
    dict to also let a monster's innate spellcasting draw on a campaign's
    custom Spell Library entries. ``party_size`` caps how many targets a
    genuine AoE spell can hit (see :func:`app.engine.spells.targets_hit`).

    A monster's baseline ``attacks`` fire every round *unless displaced* -
    the same idea as a character casting a leveled spell instead of their
    cantrip. ``save_attacks`` (breath weapons) and innate ``spells`` default
    to ``displaces_action: True``: a dragon doesn't bite AND breathe fire
    the same turn, so each use of one of these replaces one round's worth
    of the monster's own attacks rather than stacking on top of them.
    ``legendary_actions`` never displace - they fire on *other* creatures'
    turns, genuinely in addition to the monster's own turn, which is the
    whole point of them being "legendary."

    Everything else it can do isn't guaranteed every round, so each is
    keyed by name in ``special_uses`` as a plain **total expected uses for
    this whole encounter** (not a per-round rate) - "I expect the dragon to
    breathe fire once this fight" is entered as ``1``, not a fraction. That
    total is capped at ``rounds_assumed`` (a monster can't use a special
    ability more times than it has turns - set the number very high to mean
    "every round," and it'll clamp there rather than inflating the damage
    beyond what's physically possible) and divided by ``rounds_assumed`` to
    fold it into the per-round rate everything else is expressed in. Falls
    back to each ability's own ``default_uses_per_encounter`` (a plain
    suggested guess, not a source of truth) when ``special_uses`` doesn't
    have an entry for it - the real number is meant to be set per-encounter,
    not baked into the stat block.
    """
    registry = spells_registry if spells_registry is not None else SPELLS
    special_uses = special_uses or {}
    rounds_assumed = max(1, rounds_assumed)
    components: list[dict] = []
    special_components: list[dict] = []
    displacing_uses = 0.0

    for a in monster.get("save_attacks", []):
        name = a.get("name", "Save Attack")
        total_uses = special_uses.get(name, a.get("default_uses_per_encounter", 1))
        if total_uses <= 0:
            continue
        effective_uses = min(total_uses, rounds_assumed)
        ability = a.get("save_ability", "dex")
        success = hit_chance(target_save_bonuses.get(ability, 0), a["dc"])
        d = die_avg(a["die_count"], a["die_sides"]) + a.get("flat_bonus", 0)
        per_use = (1 - success) * d + success * (d * 0.5 if a.get("half_on_save") else 0)
        if a.get("displaces_action", True):
            displacing_uses += effective_uses
        special_components.append({"name": name, "type": a["damage_type"], "magical": bool(a.get("magical")),
                                    "amount": effective_uses * per_use / rounds_assumed})

    for s in monster.get("spells", []):
        spell = registry.get(s.get("spell_id"))
        if not spell:
            continue
        name = f"{spell['name']} (innate)"
        total_uses = special_uses.get(name, s.get("default_uses_per_encounter", 1))
        if total_uses <= 0:
            continue
        effective_uses = min(total_uses, rounds_assumed)
        if spell["mode"] == "save":
            ability = spell.get("save_ability", "dex")
            per_cast = expected_leveled_spell_damage(
                spell, spell["level"], save_dc=s.get("spell_save_dc", 10),
                target_save_bonus=target_save_bonuses.get(ability, 0),
            )
        else:
            per_cast = expected_leveled_spell_damage(
                spell, spell["level"], attack_bonus=s.get("spell_attack_bonus", 0), target_ac=target_ac,
            )
        per_cast *= targets_hit(spell, party_size)
        if s.get("displaces_action", True):
            displacing_uses += effective_uses
        special_components.append({"name": name, "type": spell["damage_type"], "magical": True,
                                    "amount": effective_uses * per_cast / rounds_assumed})

    # Legendary actions are computed AFTER displacement is tallied, since
    # they never contribute to it - they fire on other creatures' turns,
    # not instead of the monster's own.
    for a in monster.get("legendary_actions", []) if monster.get("is_legendary") else []:
        name = f"{a.get('name', 'Legendary Action')} (legendary)"
        total_uses = special_uses.get(name, a.get("default_uses_per_encounter", 1))
        if total_uses <= 0:
            continue
        effective_uses = min(total_uses, rounds_assumed)
        per_use = expected_attack_damage(
            a["to_hit"], target_ac, die_avg(a["die_count"], a["die_sides"]), a.get("flat_bonus", 0),
        )
        special_components.append({"name": name, "type": a["damage_type"], "magical": bool(a.get("magical")),
                                    "amount": effective_uses * per_use / rounds_assumed})

    displaced_fraction = min(1.0, displacing_uses / rounds_assumed)
    for a in monster.get("attacks", []):
        per_attack = expected_attack_damage(
            a["to_hit"], target_ac, die_avg(a["die_count"], a["die_sides"]), a.get("flat_bonus", 0),
        )
        amount = a.get("count", 1) * per_attack * (1 - displaced_fraction)
        components.append({"name": a.get("name", "Attack"), "type": a["damage_type"],
                            "magical": bool(a.get("magical")), "amount": amount})

    components += special_components
    total_dpr = sum(c["amount"] for c in components)
    return {"components": components, "total_dpr": total_dpr}
