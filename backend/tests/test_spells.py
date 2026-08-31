import math

import pytest

from app.engine.spells import (
    SPELLS,
    cantrip_tier_multiplier,
    dice_avg_for_slot,
    estimate_aoe_targets,
    expected_cantrip_damage,
    expected_leveled_spell_damage,
    merge_spell_registry,
    targets_hit,
)


def test_dice_avg_for_slot_at_base_level():
    assert dice_avg_for_slot(SPELLS["fireball"], slot_level=3) == 28.0


def test_dice_avg_for_slot_upcast():
    # Fireball upcast to a 5th-level slot: +1d6 (avg 3.5) per level above 3rd.
    assert dice_avg_for_slot(SPELLS["fireball"], slot_level=5) == pytest.approx(28.0 + 2 * 3.5)


def test_auto_hit_spell_ignores_target_ac_and_save_dc():
    dmg = expected_leveled_spell_damage(SPELLS["magic_missile"], slot_level=1, target_ac=999, save_dc=999)
    assert dmg == pytest.approx(10.5)


def test_attack_mode_spell_uses_hit_chance_and_crits():
    dmg = expected_leveled_spell_damage(SPELLS["scorching_ray"], slot_level=2, attack_bonus=6, target_ac=15)
    # +6 vs AC15 = 60% hit (5% of which crits), base_avg 21 at 2nd level.
    assert dmg == pytest.approx(0.55 * 21 + 0.05 * 42)


def test_save_mode_spell_with_half_on_save():
    dmg = expected_leveled_spell_damage(SPELLS["fireball"], slot_level=3, save_dc=15, target_save_bonus=5)
    # target needs a 10+ to save (55% success), half damage on a success.
    assert dmg == pytest.approx(0.45 * 28 + 0.55 * 14)


def test_save_mode_spell_without_half_on_save_deals_zero_on_a_success():
    dmg = expected_leveled_spell_damage(SPELLS["disintegrate"], slot_level=6, save_dc=15, target_save_bonus=15)
    # target auto-succeeds (bonus == DC -> only a nat 1 fails, i.e. 5%)
    assert dmg == pytest.approx(0.05 * 75.0)


def test_cantrip_tier_multiplier_progression():
    assert cantrip_tier_multiplier(1) == 1
    assert cantrip_tier_multiplier(5) == 2
    assert cantrip_tier_multiplier(11) == 3
    assert cantrip_tier_multiplier(17) == 4


def test_eldritch_blast_scales_beam_count_not_die_size():
    low = expected_cantrip_damage(SPELLS["eldritch_blast"], char_level=1, attack_bonus=6, target_ac=15)
    high = expected_cantrip_damage(SPELLS["eldritch_blast"], char_level=17, attack_bonus=6, target_ac=15)
    # 4 beams at level 17 should be roughly 4x a single beam at level 1 (same per-beam math).
    assert high == pytest.approx(low * 4)


def test_normal_cantrip_scales_dice_not_instance_count():
    low = expected_cantrip_damage(SPELLS["fire_bolt"], char_level=1, attack_bonus=6, target_ac=15)
    high = expected_cantrip_damage(SPELLS["fire_bolt"], char_level=17, attack_bonus=6, target_ac=15)
    assert high == pytest.approx(low * 4)


# ---- spell library / custom spells ----

def test_merge_spell_registry_includes_built_ins_by_default():
    registry = merge_spell_registry(None)
    assert "fireball" in registry
    assert registry["fireball"] == SPELLS["fireball"]


def test_merge_spell_registry_adds_custom_spells():
    custom = [{"id": "homebrew-blast", "name": "Homebrew Blast", "level": 2, "damage_type": "necrotic",
               "mode": "attack", "base_avg": 15.0, "per_level_avg": 5.0}]
    registry = merge_spell_registry(custom)
    assert "homebrew-blast" in registry
    assert "fireball" in registry  # built-ins still present alongside it


def test_merge_spell_registry_ignores_entries_without_an_id():
    registry = merge_spell_registry([{"name": "Nameless (no id)", "level": 1}])
    assert len(registry) == len(SPELLS)


def test_custom_spell_damage_math_works_like_a_built_in_spell():
    custom = {"id": "homebrew-blast", "level": 2, "damage_type": "necrotic",
              "mode": "save", "save_ability": "con", "half_on_save": True, "base_avg": 20.0, "per_level_avg": 5.0}
    dmg = expected_leveled_spell_damage(custom, slot_level=4, save_dc=15, target_save_bonus=5)
    # same formula as any built-in save spell: needs a 10+ (55% success), half damage on a success
    expected = 0.45 * 30.0 + 0.55 * 15.0
    assert dmg == pytest.approx(expected)


# ---- AoE target counting ----

def test_single_target_spell_always_hits_exactly_one_target():
    assert targets_hit(SPELLS["disintegrate"], available_targets=1) == 1
    assert targets_hit(SPELLS["disintegrate"], available_targets=20) == 1


def test_aoe_spell_scales_up_to_its_own_cap():
    assert targets_hit(SPELLS["fireball"], available_targets=1) == 1
    assert targets_hit(SPELLS["fireball"], available_targets=2) == 2
    assert targets_hit(SPELLS["fireball"], available_targets=3) == 3


def test_aoe_spell_never_exceeds_its_own_cap_no_matter_how_many_targets_exist():
    assert targets_hit(SPELLS["fireball"], available_targets=100) == 3


def test_targets_hit_never_returns_less_than_one():
    assert targets_hit(SPELLS["fireball"], available_targets=0) == 1


# ---- shape-aware AoE estimation ----

def test_a_line_hits_fewer_targets_than_a_sphere_of_a_comparable_size_stat():
    # This is the whole point: a narrow beam/line covers far less ground
    # than a sphere or cube, even when its "size" number looks big.
    line = estimate_aoe_targets("line", size=60, width=5)
    sphere = estimate_aoe_targets("sphere", size=20)
    assert line < sphere


def test_sunbeam_is_a_line_not_a_sphere_and_hits_accordingly():
    # Sunbeam is a 60-ft line, 5 ft wide - real area is tiny compared to
    # Fireball's 20-ft-radius sphere, even though it's a higher-level spell.
    assert SPELLS["sunbeam"]["shape"] == "line"
    assert targets_hit(SPELLS["sunbeam"], available_targets=20) < targets_hit(SPELLS["fireball"], available_targets=20)


def test_larger_cone_hits_more_targets_than_a_smaller_cone():
    small_cone = estimate_aoe_targets("cone", size=15)
    large_cone = estimate_aoe_targets("cone", size=60)
    assert large_cone > small_cone


def test_sphere_area_scales_with_radius_squared():
    # Doubling the radius quadruples the area, not just doubles the target
    # count - use radii big enough that the floor-of-2 minimum (see below)
    # isn't masking the scaling.
    small = estimate_aoe_targets("sphere", size=20)
    big = estimate_aoe_targets("sphere", size=40)
    assert big >= small * 3  # roughly 4x area -> meaningfully more than 2x targets


def test_aoe_estimate_never_goes_below_two_targets():
    # No reasonable DM burns an area-of-effect spell on a single target -
    # even a tiny cone/line still models "a small cluster," not "one guy."
    assert estimate_aoe_targets("cone", size=5) == 2
    assert estimate_aoe_targets("line", size=10, width=5) == 2
    assert estimate_aoe_targets("sphere", size=1) == 2


def test_aoe_floor_does_not_override_how_many_targets_actually_exist():
    # The floor sets the typical assumption, not physical reality - if only
    # one enemy is actually in this specific fight, that's still all it hits.
    tiny_line = {"aoe_targets": None, "shape": "line", "size": 10}
    assert targets_hit(tiny_line, available_targets=1) == 1


def test_cube_uses_side_squared_as_area():
    assert estimate_aoe_targets("cube", size=20) == estimate_aoe_targets("sphere", size=math.sqrt(400 / math.pi))


def test_unknown_shape_falls_back_to_a_single_target():
    assert estimate_aoe_targets("donut", size=100) == 1


def test_explicit_aoe_targets_overrides_shape_based_estimation():
    # Chain Lightning's targeting is an explicit rule (primary + N more),
    # not a real area, so it keeps a manual override instead of a shape.
    assert "shape" not in SPELLS["chain_lightning"]
    assert SPELLS["chain_lightning"]["aoe_targets"] > 1


def test_single_target_spell_has_no_shape_or_aoe_targets():
    assert "shape" not in SPELLS["disintegrate"]
    assert "aoe_targets" not in SPELLS["disintegrate"]
