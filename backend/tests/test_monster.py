import pytest

from app.engine.monster import CR_SEED, compute_monster_profile, seed_monster_from_cr


def test_seed_monster_from_cr_produces_a_plausible_starting_block():
    seeded = seed_monster_from_cr("5")
    assert seeded["ac"] == CR_SEED["5"]["ac"]
    assert seeded["max_hp"] == CR_SEED["5"]["hp"]
    assert seeded["xp"] == CR_SEED["5"]["xp"]
    assert len(seeded["attacks"]) == 1
    # every ability seeded so a fresh monster works with the per-ability save system immediately
    assert set(seeded["save_bonuses"].keys()) == {"str", "dex", "con", "int", "wis", "cha"}


def test_single_attack_dpr_matches_hand_calculation():
    monster = {
        "attacks": [{
            "name": "Claw", "count": 2, "to_hit": 6, "die_count": 1, "die_sides": 8,
            "flat_bonus": 4, "damage_type": "slashing", "magical": False,
        }],
    }
    profile = compute_monster_profile(monster, target_ac=15, target_save_bonuses={})
    # +6 vs AC15 -> needs 9+ -> 60% hit, 5% of which crit. 1d8 avg 4.5.
    per_hit, per_crit = 4.5 + 4, 9 + 4
    expected = 2 * (0.05 * per_crit + 0.55 * per_hit)
    assert profile["total_dpr"] == pytest.approx(expected)


def test_baseline_attacks_are_not_divided_by_rounds_assumed():
    # Attacks fire every round unconditionally - the rounds_assumed divisor
    # only applies to the "special ability" categories below.
    monster = {"attacks": [{
        "name": "Claw", "count": 1, "to_hit": 6, "die_count": 1, "die_sides": 8,
        "flat_bonus": 0, "damage_type": "slashing", "magical": False,
    }]}
    short = compute_monster_profile(monster, 15, {}, rounds_assumed=1)
    long = compute_monster_profile(monster, 15, {}, rounds_assumed=5)
    assert short["total_dpr"] == pytest.approx(long["total_dpr"])


def test_save_attack_checks_its_own_specific_ability():
    monster = {
        "attacks": [],
        "save_attacks": [{
            "name": "Fire Breath", "dc": 15, "die_count": 8, "die_sides": 6, "save_ability": "dex",
            "flat_bonus": 0, "damage_type": "fire", "magical": True, "half_on_save": True,
            "default_uses_per_encounter": 1,
        }],
    }
    # target's Dex save bonus +5 vs DC 15 -> needs a 10+ -> 55% success.
    # A Wisdom save bonus in the dict should be ignored entirely - this attack cares about Dex.
    profile = compute_monster_profile(monster, target_ac=15, target_save_bonuses={"dex": 5, "wis": 99}, rounds_assumed=1)
    avg_dmg = 8 * 3.5
    expected = 0.45 * avg_dmg + 0.55 * (avg_dmg * 0.5)
    assert profile["total_dpr"] == pytest.approx(expected)


def test_save_attack_expected_uses_is_a_total_for_the_encounter_not_a_rate():
    # Spending 1 use across a 1-round vs a 4-round assumed fight should give
    # a smaller PER-ROUND rate the longer the fight is assumed to run,
    # since the total damage this encounter is fixed at one use.
    monster = {"attacks": [], "save_attacks": [{
        "name": "Fire Breath", "dc": 15, "die_count": 8, "die_sides": 6, "save_ability": "dex",
        "flat_bonus": 0, "damage_type": "fire", "magical": True, "half_on_save": True,
        "default_uses_per_encounter": 1,
    }]}
    short_fight = compute_monster_profile(monster, 15, {"dex": 0}, rounds_assumed=1)
    long_fight = compute_monster_profile(monster, 15, {"dex": 0}, rounds_assumed=4)
    assert short_fight["total_dpr"] == pytest.approx(long_fight["total_dpr"] * 4)


def test_save_attack_special_uses_override_replaces_the_bestiary_default():
    monster = {"attacks": [], "save_attacks": [{
        "name": "Fire Breath", "dc": 15, "die_count": 8, "die_sides": 6, "save_ability": "dex",
        "flat_bonus": 0, "damage_type": "fire", "magical": True, "half_on_save": True,
        "default_uses_per_encounter": 1,
    }]}
    # rounds_assumed=5 is bigger than both 1 and 3, so the uses-cap below doesn't interfere.
    default_used = compute_monster_profile(monster, 15, {"dex": 0}, rounds_assumed=5)
    overridden = compute_monster_profile(monster, 15, {"dex": 0}, special_uses={"Fire Breath": 3}, rounds_assumed=5)
    assert overridden["total_dpr"] == pytest.approx(default_used["total_dpr"] * 3)


def test_save_attack_with_zero_expected_uses_contributes_nothing():
    monster = {"attacks": [], "save_attacks": [{
        "name": "Fire Breath", "dc": 15, "die_count": 8, "die_sides": 6, "save_ability": "dex",
        "flat_bonus": 0, "damage_type": "fire", "magical": True, "half_on_save": True,
        "default_uses_per_encounter": 1,
    }]}
    profile = compute_monster_profile(monster, 15, {"dex": 0}, special_uses={"Fire Breath": 0})
    assert profile["total_dpr"] == 0


def test_save_attack_defaults_to_dex_when_ability_not_specified():
    monster = {"attacks": [], "save_attacks": [{
        "name": "Unlabeled Blast", "dc": 15, "die_count": 4, "die_sides": 6,
        "flat_bonus": 0, "damage_type": "force", "magical": True, "half_on_save": True,
    }]}
    with_dex = compute_monster_profile(monster, 15, {"dex": 5})
    with_only_wis = compute_monster_profile(monster, 15, {"wis": 5})
    # missing "dex" in the second dict falls back to 0, so it should deal MORE damage
    assert with_only_wis["total_dpr"] > with_dex["total_dpr"]


def test_save_attack_no_damage_on_save_when_half_on_save_is_false():
    monster = {
        "attacks": [],
        "save_attacks": [{
            "name": "Banishing Glare", "dc": 15, "die_count": 4, "die_sides": 6, "save_ability": "wis",
            "flat_bonus": 0, "damage_type": "radiant", "magical": True, "half_on_save": False,
            "default_uses_per_encounter": 1,
        }],
    }
    profile = compute_monster_profile(monster, target_ac=15, target_save_bonuses={"wis": 5}, rounds_assumed=1)
    avg_dmg = 4 * 3.5
    expected = 0.45 * avg_dmg  # 0 damage on the 55% that succeed
    assert profile["total_dpr"] == pytest.approx(expected)


def test_legendary_actions_only_count_for_legendary_monsters():
    base = {
        "attacks": [],
        "legendary_actions": [{
            "name": "Tail Attack", "default_uses_per_encounter": 3, "to_hit": 10,
            "die_count": 2, "die_sides": 8, "flat_bonus": 6,
            "damage_type": "bludgeoning", "magical": True,
        }],
    }
    non_legendary = compute_monster_profile({**base, "is_legendary": False}, 17, {})
    legendary = compute_monster_profile({**base, "is_legendary": True}, 17, {})
    assert non_legendary["total_dpr"] == 0
    assert legendary["total_dpr"] > 0


def test_legendary_action_expected_uses_is_a_total_for_the_encounter():
    monster = {"attacks": [], "is_legendary": True, "legendary_actions": [{
        "name": "Tail Attack", "default_uses_per_encounter": 2, "to_hit": 10,
        "die_count": 2, "die_sides": 8, "flat_bonus": 6, "damage_type": "bludgeoning", "magical": True,
    }]}
    # 2 total uses across a 3-round fight vs a 6-round fight (both well above
    # 2, so the uses-cap below doesn't kick in) - same total damage, so the
    # per-round rate should be exactly half in the longer one.
    three_round = compute_monster_profile(monster, 17, {}, rounds_assumed=3)
    six_round = compute_monster_profile(monster, 17, {}, rounds_assumed=6)
    assert three_round["total_dpr"] == pytest.approx(six_round["total_dpr"] * 2)


def test_legendary_action_special_uses_override_replaces_the_bestiary_default():
    monster = {"attacks": [], "is_legendary": True, "legendary_actions": [{
        "name": "Tail Attack", "default_uses_per_encounter": 3, "to_hit": 10,
        "die_count": 2, "die_sides": 8, "flat_bonus": 6, "damage_type": "bludgeoning", "magical": True,
    }]}
    # rounds_assumed=5 is bigger than both 3 and 1, so the uses-cap below
    # doesn't interfere with what this test is actually checking.
    default_used = compute_monster_profile(monster, 17, {}, rounds_assumed=5)
    overridden = compute_monster_profile(monster, 17, {}, special_uses={"Tail Attack (legendary)": 1}, rounds_assumed=5)
    # "if you expect the boss to use it once in an encounter, it should only be added once"
    assert overridden["total_dpr"] == pytest.approx(default_used["total_dpr"] / 3)


def test_innate_spellcasting_attack_mode():
    monster = {
        "attacks": [],
        "spells": [{"spell_id": "fire_bolt", "default_uses_per_encounter": 1, "spell_attack_bonus": 6}],
    }
    profile = compute_monster_profile(monster, target_ac=15, target_save_bonuses={}, rounds_assumed=1)
    # Fire Bolt with no upcasting: base_avg 5.5, +6 vs AC15 = 60% hit (5% crit).
    expected = 0.05 * (2 * 5.5) + 0.55 * 5.5
    assert profile["total_dpr"] == pytest.approx(expected)
    assert profile["components"][0]["type"] == "fire"


def test_innate_spellcasting_save_mode_checks_the_spells_own_ability():
    monster = {
        "attacks": [],
        "spells": [{"spell_id": "fireball", "default_uses_per_encounter": 1, "spell_save_dc": 15}],
    }
    # Fireball checks Dex - a huge Wisdom bonus in the dict should not help the target at all.
    vulnerable = compute_monster_profile(monster, 15, {"dex": 0, "wis": 20})
    protected = compute_monster_profile(monster, 15, {"dex": 20, "wis": 0})
    assert vulnerable["total_dpr"] > protected["total_dpr"]


def test_innate_spellcasting_respects_zero_expected_uses():
    monster = {"attacks": [], "spells": [{"spell_id": "fire_bolt", "default_uses_per_encounter": 0, "spell_attack_bonus": 6}]}
    profile = compute_monster_profile(monster, 15, {})
    assert profile["total_dpr"] == 0


def test_innate_spellcasting_expected_uses_is_a_total_for_the_encounter():
    monster = {"attacks": [], "spells": [{"spell_id": "fire_bolt", "default_uses_per_encounter": 2, "spell_attack_bonus": 6}]}
    # rounds_assumed=3/6 are both bigger than 2 uses, so the uses-cap below doesn't interfere.
    short_fight = compute_monster_profile(monster, 15, {}, rounds_assumed=3)
    long_fight = compute_monster_profile(monster, 15, {}, rounds_assumed=6)
    assert short_fight["total_dpr"] == pytest.approx(long_fight["total_dpr"] * 2)


def test_unknown_spell_id_is_silently_skipped_not_a_crash():
    monster = {"attacks": [], "spells": [{"spell_id": "not-a-real-spell", "default_uses_per_encounter": 1}]}
    profile = compute_monster_profile(monster, 15, {})
    assert profile["total_dpr"] == 0


# ---- attack displacement: a monster only gets one action per turn ----

def _biting_breathing_dragon(**overrides):
    monster = {
        "attacks": [{"name": "Bite", "count": 2, "to_hit": 10, "die_count": 2, "die_sides": 10,
                     "flat_bonus": 6, "damage_type": "piercing", "magical": True}],
        "save_attacks": [{"name": "Fire Breath", "dc": 18, "die_count": 12, "die_sides": 6, "save_ability": "dex",
                           "flat_bonus": 0, "damage_type": "fire", "magical": True, "half_on_save": True,
                           "default_uses_per_encounter": 2}],
    }
    monster.update(overrides)
    return monster


def test_save_attack_displaces_the_monsters_own_baseline_attacks():
    dragon = _biting_breathing_dragon()
    profile = compute_monster_profile(dragon, target_ac=16, target_save_bonuses={"dex": 3}, rounds_assumed=4)
    bite = next(c for c in profile["components"] if c["name"] == "Bite")
    no_breath = compute_monster_profile({**dragon, "save_attacks": []}, target_ac=16, target_save_bonuses={"dex": 3}, rounds_assumed=4)
    full_bite = next(c for c in no_breath["components"] if c["name"] == "Bite")
    # breathing fire twice in a 4-round fight displaces half the bite rounds
    assert bite["amount"] == pytest.approx(full_bite["amount"] * 0.5)


def test_save_attack_can_be_marked_non_displacing():
    dragon = _biting_breathing_dragon()
    dragon["save_attacks"][0]["displaces_action"] = False
    profile = compute_monster_profile(dragon, target_ac=16, target_save_bonuses={"dex": 3}, rounds_assumed=4)
    bite = next(c for c in profile["components"] if c["name"] == "Bite")
    full_bite_amount = compute_monster_profile({**dragon, "save_attacks": []}, 16, {"dex": 3}, rounds_assumed=4)
    assert bite["amount"] == pytest.approx(next(c for c in full_bite_amount["components"] if c["name"] == "Bite")["amount"])


def test_innate_spell_also_displaces_baseline_attacks_by_default():
    monster = {
        "attacks": [{"name": "Claw", "count": 1, "to_hit": 6, "die_count": 1, "die_sides": 6,
                     "flat_bonus": 3, "damage_type": "slashing", "magical": False}],
        "spells": [{"spell_id": "fire_bolt", "default_uses_per_encounter": 1, "spell_attack_bonus": 6}],
    }
    profile = compute_monster_profile(monster, target_ac=15, target_save_bonuses={}, rounds_assumed=2)
    claw = next(c for c in profile["components"] if c["name"] == "Claw")
    full_claw = compute_monster_profile({**monster, "spells": []}, 15, {}, rounds_assumed=2)
    assert claw["amount"] == pytest.approx(next(c for c in full_claw["components"] if c["name"] == "Claw")["amount"] * 0.5)


def test_legendary_actions_never_displace_baseline_attacks():
    monster = {
        "is_legendary": True,
        "attacks": [{"name": "Bite", "count": 2, "to_hit": 10, "die_count": 2, "die_sides": 10,
                     "flat_bonus": 6, "damage_type": "piercing", "magical": True}],
        "legendary_actions": [{"name": "Tail Attack", "to_hit": 10, "die_count": 2, "die_sides": 8,
                                 "flat_bonus": 6, "damage_type": "bludgeoning", "magical": True,
                                 "default_uses_per_encounter": 3}],
    }
    profile = compute_monster_profile(monster, target_ac=16, target_save_bonuses={}, rounds_assumed=3)
    bite = next(c for c in profile["components"] if c["name"] == "Bite")
    no_legendary = compute_monster_profile({**monster, "legendary_actions": []}, 16, {}, rounds_assumed=3)
    full_bite = next(c for c in no_legendary["components"] if c["name"] == "Bite")
    assert bite["amount"] == pytest.approx(full_bite["amount"])  # unaffected - legendary actions fire on OTHER turns


def test_displacement_from_multiple_special_abilities_stacks():
    monster = {
        "attacks": [{"name": "Bite", "count": 4, "to_hit": 10, "die_count": 1, "die_sides": 6,
                     "flat_bonus": 3, "damage_type": "piercing", "magical": True}],
        "save_attacks": [
            {"name": "Fire Breath", "dc": 18, "die_count": 1, "die_sides": 6, "default_uses_per_encounter": 1,
             "damage_type": "fire", "magical": True, "half_on_save": True},
            {"name": "Frost Breath", "dc": 18, "die_count": 1, "die_sides": 6, "default_uses_per_encounter": 1,
             "damage_type": "cold", "magical": True, "half_on_save": True},
        ],
    }
    profile = compute_monster_profile(monster, target_ac=16, target_save_bonuses={}, rounds_assumed=4)
    bite = next(c for c in profile["components"] if c["name"] == "Bite")
    full_bite = compute_monster_profile({**monster, "save_attacks": []}, 16, {}, rounds_assumed=4)
    # 1 + 1 = 2 total displacing uses out of 4 rounds -> half the bite rounds displaced
    assert bite["amount"] == pytest.approx(next(c for c in full_bite["components"] if c["name"] == "Bite")["amount"] * 0.5)


def test_displacement_cannot_reduce_attacks_below_zero():
    # More displacing uses than rounds assumed shouldn't produce negative damage.
    dragon = _biting_breathing_dragon()
    dragon["save_attacks"][0]["default_uses_per_encounter"] = 10
    profile = compute_monster_profile(dragon, target_ac=16, target_save_bonuses={"dex": 3}, rounds_assumed=2)
    bite = next(c for c in profile["components"] if c["name"] == "Bite")
    assert bite["amount"] == pytest.approx(0)


def test_setting_uses_very_high_caps_at_firing_every_round_not_inflated_damage():
    # "Set the number very high to mean 'every round'" should genuinely mean
    # that - a monster physically cannot use a special ability more times
    # than it has turns, so an absurd number must clamp down to
    # rounds_assumed, not multiply the damage by hundreds.
    monster = {"attacks": [], "save_attacks": [{
        "name": "Fire Breath", "dc": 15, "die_count": 8, "die_sides": 6, "save_ability": "dex",
        "flat_bonus": 0, "damage_type": "fire", "magical": True, "half_on_save": True,
        "default_uses_per_encounter": 999,
    }]}
    inflated_input = compute_monster_profile(monster, 15, {"dex": 0}, rounds_assumed=5)
    fires_every_round = compute_monster_profile(
        {**monster, "save_attacks": [{**monster["save_attacks"][0], "default_uses_per_encounter": 1}]},
        15, {"dex": 0}, rounds_assumed=1,
    )
    # 999 uses in a 5-round fight should equal exactly "fires every round" -
    # not ~200x that.
    assert inflated_input["total_dpr"] == pytest.approx(fires_every_round["total_dpr"])
