"""A curated list of SRD-legal damage-dealing spells, used so a character's
spell-slot resources deal *real* spell damage (with upcasting) instead of a
single generic "average spell damage" number.

This is intentionally not exhaustive - it covers the iconic damage spell in
most niches (single-target attack, AoE save, guaranteed-hit) per class,
which is enough for the planner to be meaningfully accurate without turning
into a full spellbook compendium. Add more by appending to ``SPELLS``.

Fields:
    level            spell level (0 = cantrip)
    classes          which class spell lists it appears on (SRD 2014)
    damage_type      one of app.engine.damage_types.DAMAGE_TYPES
    mode             "attack" (spell attack roll), "save" (target saves),
                      or "auto" (no roll at all, e.g. Magic Missile)
    save_ability     only present when mode == "save": which of the target's
                      six saves is being tested ("str"/"dex"/"con"/"int"/"wis"/"cha")
    half_on_save     only meaningful when mode == "save"
    base_avg         average damage at the spell's minimum casting level
                      (or per-tier, for cantrips - see below)
    per_level_avg    extra average damage per slot level spent above the
                      spell's minimum level (0 if the spell doesn't scale)
    beams_scale_with_tier
                      cantrip-only: True means the *number of instances*
                      scales with character level (Eldritch Blast) rather
                      than the die size/count scaling like every other
                      cantrip (Fire Bolt, Sacred Flame, ...)
    bonus_action     True if this spell's casting time is a bonus action
                      (Spiritual Weapon, Hail of Thorns) rather than a full
                      action - relevant to a resource's ``displaces_at_will``
                      default, since a bonus-action spell doesn't cost the
                      turn a cantrip/attack would have used.
    aoe_targets      an explicit override for how many targets this spell's
                      damage should be multiplied by (see :func:`targets_hit`)
                      - only needed for spells whose targeting isn't a real
                      area shape (Chain Lightning's "+3 additional targets"
                      rule). Prefer ``shape``/``size`` below for anything
                      that's an actual area of effect.
    shape            "sphere" | "cube" | "cone" | "line" | "cylinder" - the
                      spell's AoE footprint, used to estimate aoe_targets
                      from its real size instead of a hand-picked number.
    size             the shape's defining dimension in feet (sphere/cylinder
                      radius, cube side, cone/line length).
    width            line-only, defaults to 5 ft if omitted.

A genuine AoE spell (Fireball, Cone of Cold, ...) still resolves as a single
expected-damage number per cast, multiplied by a shape-and-size-aware
estimate of how many enemies it typically catches in a reasonably
spread-out fight (capped at however many actually exist in that
encounter) - not the spell's full single-round, single-target damage, and
not "hits everyone" either. See the project README for the reasoning.
"""
from __future__ import annotations

import math

from .dice_math import expected_attack_damage, hit_chance

SPELLS: dict[str, dict] = {
    # ---- Cantrips (level 0) ----
    "fire_bolt": {"name": "Fire Bolt", "level": 0, "classes": ["Wizard", "Sorcerer", "Artificer"],
                  "damage_type": "fire", "mode": "attack", "base_avg": 5.5},
    "ray_of_frost": {"name": "Ray of Frost", "level": 0, "classes": ["Wizard", "Sorcerer"],
                     "damage_type": "cold", "mode": "attack", "base_avg": 4.5},
    "chill_touch": {"name": "Chill Touch", "level": 0, "classes": ["Wizard", "Sorcerer", "Warlock"],
                    "damage_type": "necrotic", "mode": "attack", "base_avg": 4.5},
    "produce_flame": {"name": "Produce Flame", "level": 0, "classes": ["Druid"],
                       "damage_type": "fire", "mode": "attack", "base_avg": 4.5},
    "eldritch_blast": {"name": "Eldritch Blast", "level": 0, "classes": ["Warlock"],
                        "damage_type": "force", "mode": "attack", "base_avg": 5.5,
                        "beams_scale_with_tier": True},
    "sacred_flame": {"name": "Sacred Flame", "level": 0, "classes": ["Cleric"],
                      "damage_type": "radiant", "mode": "save", "save_ability": "dex", "half_on_save": False, "base_avg": 4.5},
    "toll_the_dead": {"name": "Toll the Dead", "level": 0, "classes": ["Cleric", "Wizard", "Warlock"],
                        "damage_type": "necrotic", "mode": "save", "save_ability": "wis", "half_on_save": False, "base_avg": 4.5},
    "vicious_mockery": {"name": "Vicious Mockery", "level": 0, "classes": ["Bard"],
                          "damage_type": "psychic", "mode": "save", "save_ability": "wis", "half_on_save": False, "base_avg": 2.5},

    # ---- 1st level ----
    "magic_missile": {"name": "Magic Missile", "level": 1, "classes": ["Wizard", "Sorcerer"],
                        "damage_type": "force", "mode": "auto", "base_avg": 10.5, "per_level_avg": 3.5},
    "chromatic_orb": {"name": "Chromatic Orb", "level": 1, "classes": ["Wizard", "Sorcerer"],
                        "damage_type": "fire", "mode": "attack", "base_avg": 13.5, "per_level_avg": 4.5,
                        "note": "damage type is chosen at cast time; defaults to fire"},
    "burning_hands": {"name": "Burning Hands", "level": 1, "classes": ["Wizard", "Sorcerer"],
                        "damage_type": "fire", "mode": "save", "save_ability": "dex", "half_on_save": True, "base_avg": 10.5, "per_level_avg": 3.5, "shape": "cone", "size": 15},
    "guiding_bolt": {"name": "Guiding Bolt", "level": 1, "classes": ["Cleric"],
                       "damage_type": "radiant", "mode": "attack", "base_avg": 14.0, "per_level_avg": 3.5},
    "inflict_wounds": {"name": "Inflict Wounds", "level": 1, "classes": ["Cleric"],
                          "damage_type": "necrotic", "mode": "attack", "base_avg": 16.5, "per_level_avg": 5.5},
    "hail_of_thorns": {"name": "Hail of Thorns", "level": 1, "classes": ["Ranger"],
                          "damage_type": "piercing", "mode": "save", "save_ability": "dex", "half_on_save": True, "base_avg": 5.25, "per_level_avg": 3.5, "bonus_action": True},

    # ---- 2nd level ----
    "scorching_ray": {"name": "Scorching Ray", "level": 2, "classes": ["Wizard", "Sorcerer"],
                        "damage_type": "fire", "mode": "attack", "base_avg": 21.0, "per_level_avg": 7.0},
    "melfs_acid_arrow": {"name": "Melf's Acid Arrow", "level": 2, "classes": ["Wizard"],
                           "damage_type": "acid", "mode": "attack", "base_avg": 15.0, "per_level_avg": 5.0},
    "cloud_of_daggers": {"name": "Cloud of Daggers", "level": 2, "classes": ["Wizard", "Bard"],
                           "damage_type": "slashing", "mode": "auto", "base_avg": 10.0, "per_level_avg": 5.0},
    "shatter": {"name": "Shatter", "level": 2, "classes": ["Wizard", "Sorcerer"],
                  "damage_type": "thunder", "mode": "save", "save_ability": "con", "half_on_save": True, "base_avg": 13.5, "per_level_avg": 4.5, "shape": "sphere", "size": 10},
    "moonbeam": {"name": "Moonbeam", "level": 2, "classes": ["Druid"],
                   "damage_type": "radiant", "mode": "save", "save_ability": "con", "half_on_save": True, "base_avg": 11.0, "per_level_avg": 5.5},
    "flaming_sphere": {"name": "Flaming Sphere", "level": 2, "classes": ["Wizard", "Druid"],
                         "damage_type": "fire", "mode": "save", "save_ability": "dex", "half_on_save": True, "base_avg": 7.0, "per_level_avg": 3.5},
    "spiritual_weapon": {"name": "Spiritual Weapon", "level": 2, "classes": ["Cleric"],
                           "damage_type": "force", "mode": "attack", "base_avg": 8.0, "per_level_avg": 0.0,
                           "note": "modeled as one cast's worth of bonus-action attacks, not its full ongoing duration", "bonus_action": True},

    # ---- 3rd level ----
    "fireball": {"name": "Fireball", "level": 3, "classes": ["Wizard", "Sorcerer"],
                   "damage_type": "fire", "mode": "save", "save_ability": "dex", "half_on_save": True, "base_avg": 28.0, "per_level_avg": 3.5, "shape": "sphere", "size": 20},
    "lightning_bolt": {"name": "Lightning Bolt", "level": 3, "classes": ["Wizard", "Sorcerer"],
                          "damage_type": "lightning", "mode": "save", "save_ability": "dex", "half_on_save": True, "base_avg": 28.0, "per_level_avg": 3.5, "shape": "line", "size": 100, "width": 5},
    "call_lightning": {"name": "Call Lightning", "level": 3, "classes": ["Druid"],
                          "damage_type": "lightning", "mode": "save", "save_ability": "dex", "half_on_save": True, "base_avg": 16.5, "per_level_avg": 5.5, "shape": "cylinder", "size": 5},

    # ---- 4th level ----
    "ice_storm": {"name": "Ice Storm", "level": 4, "classes": ["Wizard", "Druid"],
                    "damage_type": "cold", "mode": "save", "save_ability": "dex", "half_on_save": True, "base_avg": 23.0, "per_level_avg": 0.0, "shape": "cylinder", "size": 20},
    "wall_of_fire": {"name": "Wall of Fire", "level": 4, "classes": ["Wizard", "Druid"],
                        "damage_type": "fire", "mode": "save", "save_ability": "dex", "half_on_save": True, "base_avg": 22.5, "per_level_avg": 4.5, "aoe_targets": 2},
    "vitriolic_sphere": {"name": "Vitriolic Sphere", "level": 4, "classes": ["Wizard", "Sorcerer"],
                            "damage_type": "acid", "mode": "save", "save_ability": "dex", "half_on_save": True, "base_avg": 37.5, "per_level_avg": 5.0, "shape": "sphere", "size": 20},

    # ---- 5th level ----
    "cone_of_cold": {"name": "Cone of Cold", "level": 5, "classes": ["Wizard", "Sorcerer"],
                        "damage_type": "cold", "mode": "save", "save_ability": "con", "half_on_save": True, "base_avg": 36.0, "per_level_avg": 4.5, "shape": "cone", "size": 60},
    "insect_plague": {"name": "Insect Plague", "level": 5, "classes": ["Cleric", "Druid", "Sorcerer"],
                         "damage_type": "poison", "mode": "save", "save_ability": "con", "half_on_save": True, "base_avg": 22.0, "per_level_avg": 5.5, "shape": "sphere", "size": 20},
    "flame_strike": {"name": "Flame Strike", "level": 5, "classes": ["Cleric"],
                        "damage_type": "fire", "mode": "save", "save_ability": "dex", "half_on_save": True, "base_avg": 28.0, "per_level_avg": 3.5, "shape": "cylinder", "size": 10},

    # ---- 6th level ----
    "disintegrate": {"name": "Disintegrate", "level": 6, "classes": ["Wizard"],
                        "damage_type": "force", "mode": "save", "save_ability": "dex", "half_on_save": False, "base_avg": 75.0, "per_level_avg": 10.5},
    "chain_lightning": {"name": "Chain Lightning", "level": 6, "classes": ["Wizard", "Sorcerer"],
                           "damage_type": "lightning", "mode": "save", "save_ability": "dex", "half_on_save": True, "base_avg": 45.0, "per_level_avg": 4.5, "aoe_targets": 3},
    "sunbeam": {"name": "Sunbeam", "level": 6, "classes": ["Druid", "Sorcerer", "Wizard"],
                  "damage_type": "radiant", "mode": "save", "save_ability": "con", "half_on_save": True, "base_avg": 27.0, "per_level_avg": 0.0, "shape": "line", "size": 60, "width": 5},

    # ---- 7th level ----
    "delayed_blast_fireball": {"name": "Delayed Blast Fireball", "level": 7, "classes": ["Wizard"],
                                  "damage_type": "fire", "mode": "save", "save_ability": "dex", "half_on_save": True, "base_avg": 42.0, "per_level_avg": 3.5, "shape": "sphere", "size": 20},
    "finger_of_death": {"name": "Finger of Death", "level": 7, "classes": ["Wizard", "Sorcerer"],
                           "damage_type": "necrotic", "mode": "save", "save_ability": "con", "half_on_save": True, "base_avg": 61.5, "per_level_avg": 0.0},

    # ---- 9th level ----
    "meteor_swarm": {"name": "Meteor Swarm", "level": 9, "classes": ["Wizard", "Sorcerer"],
                        "damage_type": "fire", "mode": "save", "save_ability": "dex", "half_on_save": True, "base_avg": 70.0, "per_level_avg": 0.0,
                        "note": "single-target approximation of a multi-meteor AoE", "shape": "sphere", "size": 40},
}


def cantrip_tier_multiplier(char_level: int) -> int:
    return 4 if char_level >= 17 else 3 if char_level >= 11 else 2 if char_level >= 5 else 1


def dice_avg_for_slot(spell: dict, slot_level: int) -> float:
    """Average damage when a leveled spell is cast using a slot of ``slot_level``."""
    extra = max(0, slot_level - spell["level"])
    return spell["base_avg"] + extra * spell.get("per_level_avg", 0.0)


# Calibrated so a 20-ft-radius sphere (Fireball, the community's usual AoE
# benchmark) works out to about 3 targets in a reasonably spread-out fight -
# not packed shoulder-to-shoulder, and not "hits everyone" either.
AREA_PER_TARGET_SQFT = 400.0


def estimate_aoe_targets(shape: str, size: float, width: float = 5.0) -> int:
    """A rough, shape-aware estimate of how many targets an area of effect
    catches, from its real footprint - a narrow line or cone genuinely
    covers far less ground than a sphere or cube of a comparable size stat
    (5e cones are a right-triangle shape: width at any point equals the
    distance from the origin, so a cone's area is half of size²), which is
    why this can't be a single number picked per spell level.

    Floored at 2, not 1: no reasonable DM burns an area-of-effect spell on
    a single target - if the estimate here comes out that low, it's still
    modeling "a small cluster," not "one guy." (The final result the
    encounter actually uses, via :func:`targets_hit`, can still clamp back
    down to 1 if only one enemy genuinely exists in that specific fight -
    this floor only sets the *typical* assumption, it doesn't override
    physical reality.)
    """
    if shape in ("sphere", "cylinder"):
        area = math.pi * size ** 2
    elif shape == "cube":
        area = size ** 2
    elif shape == "cone":
        area = 0.5 * size ** 2
    elif shape == "line":
        area = size * width
    else:
        return 1
    return max(2, round(area / AREA_PER_TARGET_SQFT))


def targets_hit(spell: dict, available_targets: int) -> int:
    """How many targets a spell's damage should be multiplied by this cast.

    Single-target spells (no ``aoe_targets``/``shape`` set) always return 1.
    An explicit ``aoe_targets`` always wins (for spells whose targeting
    isn't really an area shape, like Chain Lightning's "+3 additional
    targets" rule); otherwise a ``shape``+``size`` gets estimated via
    :func:`estimate_aoe_targets`. Either way, the result never exceeds
    however many targets actually exist in this specific encounter
    (``available_targets`` - the monster count for a party's spell, or the
    party size for a monster's innate spell) - never "hits everyone."
    """
    aoe = spell.get("aoe_targets")
    if aoe is None and spell.get("shape") and spell.get("size"):
        aoe = estimate_aoe_targets(spell["shape"], spell["size"], spell.get("width", 5.0))
    return max(1, min(aoe or 1, max(1, available_targets)))


def expected_leveled_spell_damage(
    spell: dict, slot_level: int, *,
    attack_bonus: float = 0, target_ac: float = 10,
    save_dc: float = 10, target_save_bonus: float = 0,
) -> float:
    dmg = dice_avg_for_slot(spell, slot_level)
    mode = spell["mode"]
    if mode == "auto":
        return dmg
    if mode == "attack":
        return expected_attack_damage(attack_bonus, target_ac, dice_avg=dmg, flat=0)
    if mode == "save":
        success = hit_chance(target_save_bonus, save_dc)
        half = dmg * 0.5 if spell.get("half_on_save") else 0.0
        return (1 - success) * dmg + success * half
    raise ValueError(f"unknown spell mode: {mode}")


def expected_cantrip_damage(
    spell: dict, char_level: int, *,
    attack_bonus: float = 0, target_ac: float = 10,
    save_dc: float = 10, target_save_bonus: float = 0,
) -> float:
    tier = cantrip_tier_multiplier(char_level)
    if spell.get("beams_scale_with_tier"):
        instances, per_instance_dmg = tier, spell["base_avg"]
    else:
        instances, per_instance_dmg = 1, spell["base_avg"] * tier

    mode = spell["mode"]
    if mode == "attack":
        per_instance = expected_attack_damage(attack_bonus, target_ac, dice_avg=per_instance_dmg, flat=0)
    elif mode == "save":
        success = hit_chance(target_save_bonus, save_dc)
        half = per_instance_dmg * 0.5 if spell.get("half_on_save") else 0.0
        per_instance = (1 - success) * per_instance_dmg + success * half
    else:
        raise ValueError(f"unsupported cantrip mode: {mode}")
    return per_instance * instances


def merge_spell_registry(custom_spells: list[dict] | None) -> dict:
    """Combine the built-in spell list with a campaign's custom spells
    (from the Spell Library) into one lookup dict, keyed by each spell's id.
    Custom spells intentionally have no ``classes`` restriction - the user
    chose to attach them to a specific slot, so there's nothing to gate.
    """
    merged = dict(SPELLS)
    for s in custom_spells or []:
        if s.get("id"):
            merged[s["id"]] = s
    return merged
