"""Class and subclass progression tables and resource templates.

Subclass matters mechanically here, not just as flavor text:

* Only a **Battle Master** Fighter gets Superiority Dice.
* Only an **Eldritch Knight** Fighter or **Arcane Trickster** Rogue gets a
  slice of wizard-style spellcasting grafted onto a martial class.
* Every other subclass's signature feature (Frenzy, Steel Defender, ...) is
  modeled directly on the character sheet - as an extra attack, rider dice,
  a flat damage bonus, or a resource, whichever shape actually matches what
  the feature does - rather than a separate hidden per-subclass lookup.
"""
from __future__ import annotations

CLASS_LIST = [
    "Artificer", "Barbarian", "Bard", "Cleric", "Druid", "Fighter", "Monk",
    "Paladin", "Ranger", "Rogue", "Sorcerer", "Warlock", "Wizard",
]

CASTER_CLASSES = {"Wizard", "Sorcerer", "Warlock", "Bard", "Druid", "Cleric", "Artificer"}

ABILITIES = ["str", "dex", "con", "int", "wis", "cha"]

# 2014 PHB saving-throw proficiencies per class - used to auto-suggest which
# two saves a character is proficient in (still fully editable per character,
# since e.g. a feat or racial trait can grant an extra one).
SAVE_PROFICIENCIES: dict[str, list[str]] = {
    "Artificer": ["con", "int"], "Barbarian": ["str", "con"], "Bard": ["dex", "cha"],
    "Cleric": ["wis", "cha"], "Druid": ["int", "wis"], "Fighter": ["str", "con"],
    "Monk": ["str", "dex"], "Paladin": ["wis", "cha"], "Ranger": ["str", "dex"],
    "Rogue": ["dex", "int"], "Sorcerer": ["con", "cha"], "Warlock": ["wis", "cha"],
    "Wizard": ["int", "wis"],
}

# Primary spellcasting ability per class, used to default spell attack bonus
# and save DC. Eldritch Knight and Arcane Trickster both cast off Intelligence
# even though their base classes (Fighter/Rogue) aren't full casters.
CASTING_ABILITY: dict[str, str] = {
    "Wizard": "int", "Artificer": "int", "Fighter": "int", "Rogue": "int",
    "Sorcerer": "cha", "Bard": "cha", "Warlock": "cha", "Paladin": "cha",
    "Cleric": "wis", "Druid": "wis", "Ranger": "wis",
}


def ability_mod(score: int) -> int:
    """The standard D&D ability modifier: floor((score - 10) / 2)."""
    return (score - 10) // 2

# Real 2014 PHB/XGE/TCE subclass names, per class - used to populate the
# subclass picker and to key the mechanical gating/bonuses below.
SUBCLASSES: dict[str, list[str]] = {
    "Artificer": ["Alchemist", "Armorer", "Artillerist", "Battle Smith"],
    "Barbarian": ["Path of the Berserker", "Path of the Totem Warrior", "Path of the Ancestral Guardian",
                  "Path of the Storm Herald", "Path of the Zealot", "Path of the Battlerager", "Path of Wild Magic"],
    "Bard": ["College of Lore", "College of Valor", "College of Glamour", "College of Swords",
             "College of Whispers", "College of Creation", "College of Eloquence"],
    "Cleric": ["Life Domain", "Light Domain", "Nature Domain", "Tempest Domain", "Trickery Domain",
               "War Domain", "Knowledge Domain", "Death Domain", "Forge Domain", "Grave Domain",
               "Order Domain", "Peace Domain", "Twilight Domain"],
    "Druid": ["Circle of the Land", "Circle of the Moon", "Circle of Dreams", "Circle of Spores",
              "Circle of Stars", "Circle of Wildfire"],
    "Fighter": ["Champion", "Battle Master", "Eldritch Knight", "Arcane Archer", "Cavalier",
                "Samurai", "Psi Warrior", "Rune Knight"],
    "Monk": ["Way of the Open Hand", "Way of Shadow", "Way of the Four Elements", "Way of the Drunken Master",
             "Way of the Kensei", "Way of Mercy", "Way of the Astral Self"],
    "Paladin": ["Oath of Devotion", "Oath of the Ancients", "Oath of Vengeance", "Oath of Conquest",
                "Oath of Redemption", "Oath of Glory", "Oathbreaker"],
    "Ranger": ["Hunter", "Beast Master", "Gloom Stalker", "Horizon Walker", "Monster Slayer",
               "Fey Wanderer", "Swarmkeeper"],
    "Rogue": ["Thief", "Assassin", "Arcane Trickster", "Mastermind", "Swashbuckler",
              "Inquisitive", "Scout", "Phantom", "Soulknife"],
    "Sorcerer": ["Draconic Bloodline", "Wild Magic", "Divine Soul", "Shadow Magic",
                 "Storm Sorcery", "Aberrant Mind", "Clockwork Soul"],
    "Warlock": ["The Fiend", "The Archfey", "The Great Old One", "The Hexblade",
                "The Celestial", "The Fathomless", "The Genie"],
    "Wizard": ["School of Evocation", "School of Abjuration", "School of Conjuration", "School of Divination",
               "School of Enchantment", "School of Illusion", "School of Necromancy", "School of Transmutation",
               "War Magic", "Bladesinging"],
}

# Subclass-specific signature features are no longer approximated by a
# hidden hardcoded number. Every one of them already maps onto a general,
# player-editable field on the character sheet instead: a genuine extra
# attack (num_attacks), a companion/rider effect (rider dice), or a plain
# flat damage bonus the player sets themselves (flat_damage_bonus) -
# whichever shape actually matches what the feature does. A hidden lookup
# table duplicating those fields was redundant with them, and for anything
# gated on an active Rage (Berserker, Zealot, Storm Herald, Battlerager) it
# was worse than redundant - it applied unconditionally even in fights
# where Rage was never spent. See Rage's own "ongoing" resource for how a
# rage-gated bonus should actually be modeled instead.


def prof_bonus(level: int) -> int:
    return 2 + (max(1, level) - 1) // 4


# level -> [1st..9th] slot counts
FULL_CASTER_SLOTS: dict[int, list[int]] = {
    1: [2,0,0,0,0,0,0,0,0], 2: [3,0,0,0,0,0,0,0,0], 3: [4,2,0,0,0,0,0,0,0], 4: [4,3,0,0,0,0,0,0,0],
    5: [4,3,2,0,0,0,0,0,0], 6: [4,3,3,0,0,0,0,0,0], 7: [4,3,3,1,0,0,0,0,0], 8: [4,3,3,2,0,0,0,0,0],
    9: [4,3,3,3,1,0,0,0,0], 10: [4,3,3,3,2,0,0,0,0], 11: [4,3,3,3,2,1,0,0,0], 12: [4,3,3,3,2,1,0,0,0],
    13: [4,3,3,3,2,1,1,0,0], 14: [4,3,3,3,2,1,1,0,0], 15: [4,3,3,3,2,1,1,1,0], 16: [4,3,3,3,2,1,1,1,0],
    17: [4,3,3,3,2,1,1,1,1], 18: [4,3,3,3,3,1,1,1,1], 19: [4,3,3,3,3,2,1,1,1], 20: [4,3,3,3,3,2,2,1,1],
}
# Paladin / Ranger / Artificer (half-casters)
HALF_CASTER_SLOTS: dict[int, list[int]] = {
    1: [0,0,0,0,0], 2: [2,0,0,0,0], 3: [3,0,0,0,0], 4: [3,0,0,0,0], 5: [4,2,0,0,0], 6: [4,2,0,0,0],
    7: [4,3,0,0,0], 8: [4,3,0,0,0], 9: [4,3,2,0,0], 10: [4,3,2,0,0], 11: [4,3,3,0,0], 12: [4,3,3,0,0],
    13: [4,3,3,1,0], 14: [4,3,3,1,0], 15: [4,3,3,2,0], 16: [4,3,3,2,0], 17: [4,3,3,3,1], 18: [4,3,3,3,1],
    19: [4,3,3,3,2], 20: [4,3,3,3,2],
}
# Eldritch Knight / Arcane Trickster (third-casters) - ONLY these two subclasses
THIRD_CASTER_SLOTS: dict[int, list[int]] = {
    3: [2,0,0,0], 4: [3,0,0,0], 5: [3,0,0,0], 6: [3,0,0,0], 7: [4,2,0,0], 8: [4,2,0,0], 9: [4,2,0,0],
    10: [4,3,0,0], 11: [4,3,0,0], 12: [4,3,0,0], 13: [4,3,2,0], 14: [4,3,2,0], 15: [4,3,2,0],
    16: [4,3,3,0], 17: [4,3,3,0], 18: [4,3,3,0], 19: [4,3,3,1], 20: [4,3,3,1],
}
# Warlock Pact Magic recharges on a SHORT rest - a real planning wrinkle.
PACT_SLOTS: dict[int, dict[str, int]] = {
    1: {"count": 1, "level": 1}, 2: {"count": 2, "level": 1}, 3: {"count": 2, "level": 2},
    4: {"count": 2, "level": 2}, 5: {"count": 2, "level": 3}, 6: {"count": 2, "level": 3},
    7: {"count": 2, "level": 4}, 8: {"count": 2, "level": 4}, 9: {"count": 2, "level": 5},
    10: {"count": 2, "level": 5}, 11: {"count": 3, "level": 5}, 12: {"count": 3, "level": 5},
    13: {"count": 3, "level": 5}, 14: {"count": 3, "level": 5}, 15: {"count": 3, "level": 5},
    16: {"count": 3, "level": 5}, 17: {"count": 4, "level": 5}, 18: {"count": 4, "level": 5},
    19: {"count": 4, "level": 5}, 20: {"count": 4, "level": 5},
}
AVG_SPELL_DAMAGE_BY_SLOT = {1: 10.5, 2: 16, 3: 24.5, 4: 30, 5: 36, 6: 42, 7: 48, 8: 54, 9: 60}


def generic_cantrip_avg(level: int) -> float:
    """Fallback cantrip damage average when no specific cantrip is known -
    tracks a typical single-die attack cantrip like Fire Bolt."""
    dice = 4 if level >= 17 else 3 if level >= 11 else 2 if level >= 5 else 1
    return dice * 5.5


def eldritch_blast_beams(level: int) -> int:
    return 4 if level >= 17 else 3 if level >= 11 else 2 if level >= 5 else 1


def rage_uses(level: int) -> int:
    if level >= 20:
        return 999
    if level >= 17:
        return 6
    if level >= 12:
        return 5
    if level >= 6:
        return 4
    if level >= 3:
        return 3
    return 2


def superiority_dice(level: int) -> dict[str, int]:
    if level >= 15:
        return {"count": 6, "die": 12}
    if level >= 7:
        return {"count": 5, "die": 10}
    if level >= 3:
        return {"count": 4, "die": 8}
    return {"count": 0, "die": 8}


def channel_divinity_uses(level: int) -> int:
    if level >= 18:
        return 3
    if level >= 6:
        return 2
    if level >= 2:
        return 1
    return 0


def extra_attacks(cls: str, level: int) -> int:
    if cls == "Fighter":
        return 4 if level >= 20 else 3 if level >= 11 else 2 if level >= 5 else 1
    if cls in ("Barbarian", "Paladin", "Ranger", "Monk"):
        return 2 if level >= 5 else 1
    return 1


FEATS = {
    "gwm": {"label": "Great Weapon Master (-5/+10)", "to_hit": -5, "dmg": 10},
    "ss": {"label": "Sharpshooter (-5/+10)", "to_hit": -5, "dmg": 10},
    "pam": {"label": "Polearm Master (+1 bonus atk, d4)", "extra_die": 4},
    "cbe": {"label": "Crossbow Expert (+1 bonus atk, d6)", "extra_die": 6},
    "savage": {"label": "Savage Attacker (~+8% dmg)", "dmg_mult": 1.08},
    "dueling_style": {"label": "Dueling style (+2 dmg)", "flat_dmg": 2},
    "archery_style": {"label": "Archery style (+2 to hit)", "to_hit": 2},
}

# Community-optimizer calibration points, pulled from "The Optimists' Guide to
# D&D 5E Damage by Class" (public DPR spreadsheet, 2014 rules). Used purely as
# a reference note in the UI - every number the engine actually computes
# still comes from the character's own build, not from this table.
OPTIMIZER_CALIBRATION = {"Barbarian": 23, "Bard": 13, "Artificer": 14}


def _spell_slot_resources(label: str, level: int) -> list[dict]:
    """Auto-added spell-slot resources for a class/level, always created
    *empty* (``spell_id: None``) - which spell occupies a slot is a manual
    choice made per-resource in the UI, not something this engine guesses at.
    The flat ``avg_value`` is only ever a fallback for a slot nobody has
    attached a spell to yet. Marked ``displaces_at_will`` since casting a
    leveled spell uses the same action a cantrip/weapon swing would have -
    it doesn't stack on top of a full turn of at-will damage.
    """
    table = FULL_CASTER_SLOTS.get(level)
    if label in ("Ranger", "Paladin", "Artificer"):
        table = HALF_CASTER_SLOTS.get(level)
    if label in ("Eldritch Knight", "Arcane Trickster"):
        table = THIRD_CASTER_SLOTS.get(level, [0, 0, 0, 0])
    if not table:
        return []
    out = []
    for i, count in enumerate(table):
        slot_level = i + 1
        if count <= 0:
            continue
        out.append({
            "name": f"{label} Lv{slot_level} Slots", "max": count, "regen": "long", "slot_level": slot_level,
            "avg_value": AVG_SPELL_DAMAGE_BY_SLOT[slot_level], "damage_type": "force", "magical": True,
            "spell_id": None, "displaces_at_will": True,
        })
    return out


def class_resource_templates(cls: str, level: int, subclass: str | None = None) -> list[dict]:
    """The class's (and, where mechanically relevant, subclass's) default
    limited-use resources at a given level: spell slots, Rage, Ki, ..."""
    r: list[dict] = []

    if cls == "Barbarian":
        r.append({"name": "Rage", "max": rage_uses(level), "avg_value": 2, "regen": "long", "timing": "ongoing",
                   "damage_type": "weapon", "magical": False,
                   "note": "extra dmg on every hit for the whole fight while raging, same type as your weapon"})
    elif cls == "Bard":
        r.append({"name": "Bardic Inspiration", "max": 3, "avg_value": 5.5,
                   "regen": "short" if level >= 5 else "long", "damage_type": "weapon", "magical": False,
                   "note": "buff/debuff value, not direct dmg"})
        r += _spell_slot_resources("Bard", level)
    elif cls == "Cleric":
        r.append({"name": "Channel Divinity", "max": channel_divinity_uses(level), "avg_value": 20,
                   "regen": "short", "damage_type": "radiant", "magical": True})
        r += _spell_slot_resources("Cleric", level)
    elif cls == "Druid":
        r.append({"name": "Wild Shape", "max": 2, "avg_value": 0, "regen": "short",
                   "damage_type": "bludgeoning", "magical": False, "note": "utility/tankiness, not direct DPR"})
        r += _spell_slot_resources("Druid", level)
    elif cls == "Fighter":
        r.append({"name": "Action Surge", "max": 2 if level >= 17 else 1, "avg_value": 15, "regen": "short",
                   "damage_type": "weapon", "magical": False, "timing": "burst",
                   "note": "an extra copy of your own turn - set this to roughly your own at-will DPR"})
        r.append({"name": "Second Wind", "max": 1, "avg_value": 0, "regen": "short",
                   "damage_type": "weapon", "magical": False, "note": "healing, not damage"})
        if subclass == "Battle Master" and level >= 3:
            sd = superiority_dice(level)
            r.append({"name": "Superiority Dice", "max": sd["count"], "avg_value": (sd["die"] + 1) / 2 + 3,
                       "regen": "short", "damage_type": "weapon", "magical": False})
        if subclass == "Eldritch Knight" and level >= 3:
            r += _spell_slot_resources("Eldritch Knight", level)
    elif cls == "Monk":
        r.append({"name": "Ki Points", "max": level if level >= 2 else 0, "avg_value": 5, "regen": "short",
                   "damage_type": "bludgeoning", "magical": level >= 6})
    elif cls == "Paladin":
        r.append({"name": "Lay on Hands Pool", "max": level * 5, "avg_value": 0, "regen": "long",
                   "damage_type": "weapon", "magical": False, "note": "healing pool, not damage"})
        r.append({"name": "Channel Divinity", "max": channel_divinity_uses(level), "avg_value": 20,
                   "regen": "short", "damage_type": "radiant", "magical": True})
        total = sum(HALF_CASTER_SLOTS.get(level, []))
        r.append({"name": "Divine Smite (spell slots)", "max": total, "avg_value": 18, "regen": "long",
                   "damage_type": "radiant", "magical": True, "note": "~2d8 avg per slot, more vs undead/fiends"})
    elif cls == "Ranger":
        r += _spell_slot_resources("Ranger", level)
    elif cls == "Rogue":
        # Sneak Attack is an at-will effect, not a limited-use resource - it's
        # modeled as rider dice on the character sheet (see suggested_rider
        # below), not listed here.
        if subclass == "Arcane Trickster" and level >= 3:
            r += _spell_slot_resources("Arcane Trickster", level)
    elif cls == "Sorcerer":
        r.append({"name": "Sorcery Points", "max": level if level >= 2 else 0, "avg_value": 3, "regen": "long",
                   "damage_type": "force", "magical": True,
                   "note": "e.g. Metamagic (Empowered/Twinned Spell) - a burst in its own right, spendable alongside a spell slot in the same encounter without any action-economy conflict"})
        r += _spell_slot_resources("Sorcerer", level)
    elif cls == "Warlock":
        p = PACT_SLOTS[level]
        r.append({"name": f"Pact Slots (lvl {p['level']})", "max": p["count"], "slot_level": p["level"],
                   "avg_value": AVG_SPELL_DAMAGE_BY_SLOT[p["level"]], "regen": "short", "displaces_at_will": True,
                   "damage_type": "force", "magical": True, "spell_id": None,
                   "note": "recharges on a SHORT rest - plan around this"})
    elif cls == "Wizard":
        r += _spell_slot_resources("Wizard", level)
    elif cls == "Artificer":
        r += _spell_slot_resources("Artificer", level)
    return r


def sneak_attack_dice(level: int) -> int:
    """Sneak Attack dice count: 1d6 at level 1, +1d6 every 2 levels."""
    return (level + 1) // 2


def suggested_rider(cls: str, level: int) -> dict | None:
    """A class's always-on rider-dice effect (Sneak Attack, ...), if it has
    one. These are at-will, not a limited resource, so they belong on the
    character's rider_dice_count/rider_die_sides fields, not in the resource
    pool list - this is what the character-sheet UI auto-fills on resync."""
    if cls == "Rogue":
        return {
            "dice_count": sneak_attack_dice(level), "die_sides": 6,
            "note": "Sneak Attack - once/turn with advantage or an ally within 5 ft. of the target",
        }
    return None
