"""Pure-Python game-math engine: no Flask, no database, no I/O.

Everything in this package operates on plain dicts in and plain dicts out,
which is what makes it straightforward to unit test (see ``backend/tests``)
independently of the web layer, and straightforward to call from a Flask
route by just ``json.loads``-ing a request body.

Rules edition: 2014 only (see ``xp_budget.py`` for why).
"""
from .character import (
    compute_character_profile,
    profile_total,
    resolve_resource_type,
    save_bonus_for,
    spell_attack_bonus_for,
    spell_save_dc_for,
)
from .classes_data import (
    ABILITIES,
    CASTING_ABILITY,
    CLASS_LIST,
    FEATS,
    OPTIMIZER_CALIBRATION,
    SAVE_PROFICIENCIES,
    SUBCLASS_DAMAGE_BONUS,
    SUBCLASSES,
    ability_mod,
    class_resource_templates,
    extra_attacks,
    prof_bonus,
    sneak_attack_dice,
    suggested_rider,
)
from .damage_types import DAMAGE_TYPES, combined_multiplier
from .dice_math import die_avg, hit_chance
from .monster import CR_ORDER, CR_SEED, compute_monster_profile, seed_monster_from_cr
from .simulator import simulate_day
from .spells import SPELLS, merge_spell_registry
from .xp_budget import difficulty_label

__all__ = [
    "compute_character_profile", "profile_total", "resolve_resource_type",
    "save_bonus_for", "spell_attack_bonus_for", "spell_save_dc_for",
    "ABILITIES", "CASTING_ABILITY", "SAVE_PROFICIENCIES", "ability_mod",
    "CLASS_LIST", "FEATS", "OPTIMIZER_CALIBRATION", "SUBCLASSES", "SUBCLASS_DAMAGE_BONUS",
    "class_resource_templates", "extra_attacks", "prof_bonus", "sneak_attack_dice", "suggested_rider",
    "DAMAGE_TYPES", "combined_multiplier",
    "die_avg", "hit_chance",
    "CR_ORDER", "CR_SEED", "compute_monster_profile", "seed_monster_from_cr",
    "simulate_day",
    "SPELLS", "merge_spell_registry",
    "difficulty_label",
]

