import pytest

from app.engine.classes_data import SUBCLASSES, class_resource_templates, sneak_attack_dice, suggested_rider


def test_every_class_has_at_least_one_subclass_listed():
    from app.engine.classes_data import CLASS_LIST
    for cls in CLASS_LIST:
        assert len(SUBCLASSES[cls]) >= 1


def test_superiority_dice_only_granted_to_battle_master():
    battle_master = class_resource_templates("Fighter", level=5, subclass="Battle Master")
    champion = class_resource_templates("Fighter", level=5, subclass="Champion")
    assert any(r["name"] == "Superiority Dice" for r in battle_master)
    assert not any(r["name"] == "Superiority Dice" for r in champion)


def test_eldritch_knight_spell_slots_only_granted_to_that_subclass():
    eldritch_knight = class_resource_templates("Fighter", level=7, subclass="Eldritch Knight")
    champion = class_resource_templates("Fighter", level=7, subclass="Champion")
    assert any("Eldritch Knight" in r["name"] for r in eldritch_knight)
    assert not any("Eldritch Knight" in r["name"] for r in champion)


def test_arcane_trickster_spell_slots_only_granted_to_that_subclass():
    arcane_trickster = class_resource_templates("Rogue", level=5, subclass="Arcane Trickster")
    thief = class_resource_templates("Rogue", level=5, subclass="Thief")
    assert any("Arcane Trickster" in r["name"] for r in arcane_trickster)
    assert not any("Arcane Trickster" in r["name"] for r in thief)


def test_no_martial_subclass_gets_spellcasting_before_level_3():
    eldritch_knight_lvl1 = class_resource_templates("Fighter", level=1, subclass="Eldritch Knight")
    assert not any("Slots" in r["name"] for r in eldritch_knight_lvl1)


def test_spell_slots_always_start_unassigned():
    # Which spell fills a slot is a manual per-resource choice made in the
    # UI, not something this table guesses at - every slot comes back empty.
    resources = class_resource_templates("Wizard", level=5)
    lv3 = next(r for r in resources if r["name"] == "Wizard Lv3 Slots")
    assert lv3["spell_id"] is None
    assert lv3["slot_level"] == 3


def test_sneak_attack_is_not_modeled_as_a_spendable_resource():
    # Sneak Attack is at-will, not a limited-use pool - it belongs on the
    # character's rider-dice fields (see suggested_rider), not in this list.
    resources = class_resource_templates("Rogue", level=5)
    assert not any("Sneak Attack" in r["name"] for r in resources)


@pytest.mark.parametrize("level,expected_dice", [(1, 1), (2, 1), (3, 2), (5, 3), (10, 5), (20, 10)])
def test_sneak_attack_dice_progression(level, expected_dice):
    assert sneak_attack_dice(level) == expected_dice


def test_suggested_rider_for_rogue_matches_sneak_attack_progression():
    rider = suggested_rider("Rogue", level=5)
    assert rider["dice_count"] == sneak_attack_dice(5)
    assert rider["die_sides"] == 6


def test_suggested_rider_is_none_for_classes_without_an_at_will_rider():
    assert suggested_rider("Fighter", level=5) is None
