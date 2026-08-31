import pytest

from app.engine.xp_budget import difficulty_label, multiplier, party_adjusted_multiplier


@pytest.mark.parametrize("count,expected", [(1, 1.0), (2, 1.5), (3, 2.0), (6, 2.0), (7, 2.5), (10, 2.5), (14, 3.0), (15, 4.0)])
def test_multiplier_table(count, expected):
    assert multiplier(count) == expected


def test_party_adjusted_multiplier_bumps_up_for_small_parties():
    # A 6-monster fight is normally x2, but a 2-person party takes an extra step up.
    assert party_adjusted_multiplier(6, party_size=2) == 2.5


def test_party_adjusted_multiplier_bumps_down_for_large_parties():
    assert party_adjusted_multiplier(6, party_size=6) == 1.5


def test_difficulty_label_medium_boundary():
    # Level 5, 4 characters: medium threshold is 500*4=2000.
    label = difficulty_label(total_xp=2000, avg_party_level=5, party_size=4)
    assert label["text"] == "Medium"


def test_difficulty_label_deadly_boundary():
    label = difficulty_label(total_xp=1100 * 4, avg_party_level=5, party_size=4)
    assert label["text"] == "Deadly"
    assert label["tone"] == "danger"


def test_difficulty_label_below_lowest_threshold_is_trivial():
    label = difficulty_label(total_xp=1, avg_party_level=5, party_size=4)
    assert label["text"] == "Trivial"
    assert label["tone"] == "good"
