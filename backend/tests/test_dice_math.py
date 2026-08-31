import pytest

from app.engine.dice_math import crit_split, die_avg, expected_attack_damage, hit_chance


def test_hit_chance_typical():
    # +6 to hit vs AC 15 needs a 9+, i.e. 12 successful faces out of 20.
    assert hit_chance(6, 15) == pytest.approx(0.6)


def test_hit_chance_natural_1_always_misses():
    # An absurdly high bonus still can't beat a low AC on a natural 1.
    assert hit_chance(30, 10) == pytest.approx(0.95)


def test_hit_chance_natural_20_always_hits():
    # An AC so high only a natural 20 connects.
    assert hit_chance(0, 40) == pytest.approx(0.05)


def test_die_avg():
    assert die_avg(2, 6) == 7.0
    assert die_avg(1, 20) == 10.5
    assert die_avg(0, 6) == 0.0


def test_crit_split_carves_a_fixed_1_in_20():
    normal, crit = crit_split(0.6)
    assert crit == pytest.approx(0.05)
    assert normal == pytest.approx(0.55)


def test_crit_split_never_negative_when_hit_chance_is_low():
    normal, crit = crit_split(0.05)
    assert normal == pytest.approx(0.0)
    assert crit == pytest.approx(0.05)


def test_expected_attack_damage_combines_hit_and_crit():
    # +6 vs AC15 (60% hit, 5% of which crits), 2d6+4 (avg 11, crit avg 18)
    result = expected_attack_damage(bonus=6, target_ac=15, dice_avg=7, flat=4)
    assert result == pytest.approx(0.55 * 11 + 0.05 * 18)
