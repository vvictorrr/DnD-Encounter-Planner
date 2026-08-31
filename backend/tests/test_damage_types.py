from app.engine.damage_types import apply_multiplier_to_components, combined_multiplier


def test_no_entity_is_a_no_op():
    assert combined_multiplier(None, "fire", False) == 1.0


def test_plain_resistance_halves_damage():
    entity = {"resistances": [{"type": "fire", "magical_only": False}]}
    assert combined_multiplier(entity, "fire", False) == 0.5
    assert combined_multiplier(entity, "fire", True) == 0.5


def test_nonmagical_only_resistance_is_bypassed_by_magic():
    entity = {"resistances": [{"type": "slashing", "magical_only": True}]}
    assert combined_multiplier(entity, "slashing", False) == 0.5
    assert combined_multiplier(entity, "slashing", True) == 1.0


def test_vulnerability_doubles_damage():
    entity = {"vulnerabilities": [{"type": "cold", "magical_only": False}]}
    assert combined_multiplier(entity, "cold", False) == 2.0


def test_immunity_zeroes_damage_regardless_of_other_entries():
    entity = {
        "immunities": [{"type": "poison", "magical_only": False}],
        "vulnerabilities": [{"type": "poison", "magical_only": False}],
    }
    assert combined_multiplier(entity, "poison", False) == 0.0


def test_resistance_and_vulnerability_to_same_type_cancel_out():
    entity = {
        "resistances": [{"type": "necrotic", "magical_only": False}],
        "vulnerabilities": [{"type": "necrotic", "magical_only": False}],
    }
    assert combined_multiplier(entity, "necrotic", False) == 1.0


def test_unrelated_damage_type_is_unaffected():
    entity = {"resistances": [{"type": "fire", "magical_only": False}]}
    assert combined_multiplier(entity, "cold", False) == 1.0


def test_apply_multiplier_to_components_sums_after_resistance():
    components = [
        {"source": "weapon", "type": "fire", "magical": False, "amount": 10.0},
        {"source": "rider", "type": "cold", "magical": False, "amount": 4.0},
    ]
    entity = {"resistances": [{"type": "fire", "magical_only": False}]}
    # 10 * 0.5 (resisted fire) + 4 * 1 (unaffected cold) = 9.0
    assert apply_multiplier_to_components(components, entity) == 9.0
