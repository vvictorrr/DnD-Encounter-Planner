import pytest

from app.engine.character import (
    compute_character_profile,
    profile_total,
    resolve_resource_type,
    save_bonus_for,
    spell_attack_bonus_for,
    spell_save_dc_for,
)
from app.engine.classes_data import ability_mod


def _base_martial(**overrides):
    ch = {
        "level": 5, "cls": "Fighter", "attack_ability_mod": 4, "magic_weapon_bonus": 1,
        "flat_damage_bonus": 4, "num_attacks": 2, "weapon_die_count": 2, "weapon_die_sides": 6,
        "weapon_damage_type": "slashing", "attack_is_magical": True,
        "rider_dice_count": 0, "rider_die_sides": 6, "rider_damage_type": "slashing",
        "feats": {}, "is_caster": False, "use_cantrip": False, "cantrip_die_override": None,
    }
    ch.update(overrides)
    return ch


def test_martial_dpr_matches_hand_calculation():
    # +8 to hit (4 STR/DEX mod + 3 proficiency + 1 magic weapon) vs AC 15
    # needs a 7+, i.e. 70% to hit, 5 points of which are always a crit.
    # 2 attacks of 2d6+4 (avg 11 on a hit, 18 on a crit).
    ch = _base_martial()
    profile = compute_character_profile(ch, target_ac=15)
    assert profile["hit_pct"] == pytest.approx(0.7)
    expected = 2 * (0.05 * 18 + 0.65 * 11)
    assert profile_total(profile["components"]) == pytest.approx(expected)


def test_great_weapon_master_trades_accuracy_for_damage():
    ch = _base_martial(feats={"gwm": True})
    profile = compute_character_profile(ch, target_ac=15)
    # to-hit drops to +3 (45% to hit), damage per hit/crit rises by +10 flat.
    assert profile["hit_pct"] == pytest.approx(0.45)
    expected = 2 * (0.05 * 28 + 0.40 * 21)
    assert profile_total(profile["components"]) == pytest.approx(expected)


def test_rider_dice_apply_once_per_turn_not_per_attack():
    ch = _base_martial(rider_dice_count=2, rider_die_sides=6)  # e.g. Hunter's Mark
    profile = compute_character_profile(ch, target_ac=15)
    rider = next(c for c in profile["components"] if c["source"] == "rider")
    # hit_pct (0.7) * avg(2d6)=7, applied once regardless of num_attacks.
    assert rider["amount"] == pytest.approx(0.7 * 7)


def test_polearm_master_adds_a_bonus_attack_component():
    ch = _base_martial(feats={"pam": True})
    profile = compute_character_profile(ch, target_ac=15)
    sources = [c["source"] for c in profile["components"]]
    assert "Polearm Master bonus attack" in sources


def test_cantrip_mode_uses_level_scaled_dice_and_is_always_magical():
    ch = {
        "level": 5, "cls": "Wizard", "attack_ability_mod": 3, "magic_weapon_bonus": 0,
        "flat_damage_bonus": 0, "weapon_damage_type": "fire",
        "is_caster": True, "use_cantrip": True, "cantrip_die_override": None,
        "feats": {}, "rider_dice_count": 0,
    }
    profile = compute_character_profile(ch, target_ac=15)
    assert len(profile["components"]) == 1
    assert profile["components"][0]["magical"] is True
    assert profile["components"][0]["type"] == "fire"


def test_warlock_eldritch_blast_scales_beams_not_dice():
    ch = {
        "level": 11, "cls": "Warlock", "attack_ability_mod": 3, "magic_weapon_bonus": 0,
        "flat_damage_bonus": 3, "weapon_damage_type": "force",
        "is_caster": True, "use_cantrip": True, "cantrip_die_override": None,
        "feats": {}, "rider_dice_count": 0,
    }
    profile = compute_character_profile(ch, target_ac=15)
    # 3 beams at level 11 - reflected in a bigger single "cantrip" component than a 1-beam caster.
    single_beam_ch = dict(ch, level=1)
    single_profile = compute_character_profile(single_beam_ch, target_ac=15)
    assert profile_total(profile["components"]) > profile_total(single_profile["components"])


def test_resolve_resource_type_weapon_sentinel_inherits_from_character():
    ch = _base_martial()
    dtype, magical = resolve_resource_type(ch, {"damage_type": "weapon"})
    assert (dtype, magical) == ("slashing", True)


def test_resolve_resource_type_explicit_type_is_used_as_is():
    ch = _base_martial()
    dtype, magical = resolve_resource_type(ch, {"damage_type": "radiant", "magical": True})
    assert (dtype, magical) == ("radiant", True)


def test_resolve_resource_type_spell_id_overrides_the_resources_own_placeholder_type():
    # The resource dict's own "damage_type" is just a display fallback; once
    # a real spell is assigned, resistance math must use the spell's type.
    ch = _base_martial()
    dtype, magical = resolve_resource_type(ch, {"damage_type": "force", "spell_id": "fireball"})
    assert (dtype, magical) == ("fire", True)


def test_subclass_damage_bonus_applies_as_its_own_component():
    ch = _base_martial(cls="Barbarian", subclass="Path of the Berserker", weapon_damage_type="slashing")
    profile = compute_character_profile(ch, target_ac=15)
    bonus_component = next((c for c in profile["components"] if "Berserker" in c["source"]), None)
    assert bonus_component is not None
    assert bonus_component["amount"] == 15


def test_no_subclass_bonus_when_subclass_has_no_calibration():
    ch = _base_martial(cls="Barbarian", subclass="Path of the Totem Warrior")
    profile = compute_character_profile(ch, target_ac=15)
    assert not any("feature" in c["source"] for c in profile["components"])


def test_known_cantrip_uses_real_spell_math_over_the_generic_fallback():
    generic = {
        "level": 5, "cls": "Cleric", "attack_ability_mod": 3, "magic_weapon_bonus": 0,
        "flat_damage_bonus": 0, "weapon_damage_type": "radiant",
        "is_caster": True, "use_cantrip": True, "cantrip_die_override": None,
        "feats": {}, "rider_dice_count": 0, "cantrip_id": None,
    }
    with_sacred_flame = dict(generic, cantrip_id="sacred_flame")
    generic_profile = compute_character_profile(generic, target_ac=15)
    named_profile = compute_character_profile(with_sacred_flame, target_ac=15)
    # Sacred Flame is a save (not an attack roll) with no half-on-save, so it
    # should not resolve to the same source label as the generic fallback.
    assert generic_profile["components"][0]["source"] == "cantrip (generic)"
    assert named_profile["components"][0]["source"] == "cantrip (Sacred Flame)"
    assert named_profile["components"][0]["type"] == "radiant"


def test_sacred_flame_checks_the_targets_dex_save_not_a_flat_number():
    ch = {
        "level": 5, "cls": "Cleric", "attack_ability_mod": 3, "magic_weapon_bonus": 0,
        "flat_damage_bonus": 0, "weapon_damage_type": "radiant",
        "is_caster": True, "use_cantrip": True, "cantrip_die_override": None,
        "feats": {}, "rider_dice_count": 0, "cantrip_id": "sacred_flame",
    }
    weak_dex_target = compute_character_profile(ch, target_ac=15, target_save_bonuses={"dex": -2})
    strong_dex_target = compute_character_profile(ch, target_ac=15, target_save_bonuses={"dex": 10})
    assert profile_total(weak_dex_target["components"]) > profile_total(strong_dex_target["components"])


# ---- ability scores and saving throws ----

@pytest.mark.parametrize("score,expected", [(8, -1), (10, 0), (11, 0), (12, 1), (18, 4), (20, 5), (3, -4)])
def test_ability_mod_matches_standard_dnd_table(score, expected):
    assert ability_mod(score) == expected


def test_save_bonus_for_adds_proficiency_only_when_proficient():
    ch = {"level": 9, "ability_scores": {"str": 16, "dex": 12}, "saving_throw_proficiencies": ["str"]}
    # +3 STR mod, proficient (level 9 = +4 prof) -> +7. DEX: +1 mod, not proficient -> +1.
    assert save_bonus_for(ch, "str") == 7
    assert save_bonus_for(ch, "dex") == 1


def test_save_bonus_for_falls_back_to_class_proficiencies_when_unspecified():
    # No explicit saving_throw_proficiencies - Fighter's PHB proficiencies (str, con) apply.
    ch = {"level": 5, "cls": "Fighter", "ability_scores": {"str": 16, "wis": 14}}
    assert save_bonus_for(ch, "str") == ability_mod(16) + 3  # proficient
    assert save_bonus_for(ch, "wis") == ability_mod(14)       # not proficient, no class bonus


def test_save_bonus_for_defaults_missing_ability_score_to_10():
    ch = {"level": 5, "cls": "Fighter"}
    assert save_bonus_for(ch, "cha") == 0  # mod(10) = 0, and Fighter isn't proficient in Cha


def test_spell_attack_bonus_uses_casting_ability_by_default():
    ch = {"level": 9, "cls": "Wizard", "ability_scores": {"int": 18}}
    # +4 INT mod + prof bonus at level 9 (+4) = +8
    assert spell_attack_bonus_for(ch) == 8


def test_spell_attack_bonus_respects_an_explicit_override():
    ch = {"level": 9, "cls": "Wizard", "ability_scores": {"int": 18}, "spell_attack_bonus": 99}
    assert spell_attack_bonus_for(ch) == 99


def test_spell_save_dc_uses_casting_ability_by_default():
    ch = {"level": 9, "cls": "Sorcerer", "ability_scores": {"cha": 20}}
    # 8 + 5 (CHA mod) + 4 (prof at level 9) = 17
    assert spell_save_dc_for(ch) == 17
