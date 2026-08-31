import pytest

from app.engine.simulator import simulate_day


def _fighter(**overrides):
    ch = {
        "id": "f1", "name": "Fighter", "cls": "Fighter", "level": 5, "ac": 16, "max_hp": 45,
        "ability_scores": {"str": 18, "dex": 14, "con": 16, "int": 10, "wis": 10, "cha": 10},
        "attack_ability_mod": 4, "magic_weapon_bonus": 1, "flat_damage_bonus": 4,
        "num_attacks": 2, "weapon_die_count": 2, "weapon_die_sides": 6,
        "weapon_damage_type": "slashing", "attack_is_magical": True,
        "rider_dice_count": 0, "rider_die_sides": 6, "rider_damage_type": "slashing",
        "feats": {}, "is_caster": False, "use_cantrip": False, "cantrip_die_override": None,
        "resources": [], "resistances": [], "vulnerabilities": [], "immunities": [],
    }
    ch.update(overrides)
    return ch


def _goblin(monster_id="g1", **overrides):
    m = {
        "id": monster_id, "name": "Goblin", "ac": 15, "max_hp": 20, "xp": 50, "is_legendary": False,
        "attacks": [{"name": "Scimitar", "count": 1, "to_hit": 4, "die_count": 1, "die_sides": 6,
                     "flat_bonus": 2, "damage_type": "slashing", "magical": False}],
        "save_attacks": [], "legendary_actions": [], "legendary_resistances": 0,
        "resistances": [], "vulnerabilities": [], "immunities": [],
    }
    m.update(overrides)
    return m


def _encounter(monster_groups, rounds_assumed=3, spends=None, item_id="e1", name="Encounter", hp_overrides=None, monster_uses=None):
    return {"type": "encounter", "id": item_id, "name": name, "rounds_assumed": rounds_assumed,
            "monsters": monster_groups, "spends": spends or {}, "hp_overrides": hp_overrides or {},
            "monster_uses": monster_uses or {}}


def test_single_easy_fight_party_wins_comfortably():
    party = [_fighter()]
    bestiary = [_goblin()]
    items = [_encounter([{"bestiary_id": "g1", "count": 1}])]
    result = simulate_day(party, bestiary, items)
    snap = result["snapshots"][0]
    assert snap["rounds_to_kill_monsters"] < snap["rounds_to_drop_pc"]
    assert snap["label"]["text"] in ("Trivial", "Easy")


def test_hp_carries_forward_between_encounters_without_a_rest():
    party = [_fighter(max_hp=10)]  # deliberately fragile to force visible damage
    bestiary = [_goblin()]
    items = [
        _encounter([{"bestiary_id": "g1", "count": 1}], item_id="e1"),
        _encounter([{"bestiary_id": "g1", "count": 1}], item_id="e2"),
    ]
    result = simulate_day(party, bestiary, items)
    hp_after_first = result["snapshots"][0]["hp_after"]["f1"]
    assert hp_after_first <= 10
    # second encounter's incoming damage is computed from whatever HP survived, not a fresh 10
    hp_after_second = result["snapshots"][1]["hp_after"]["f1"]
    assert hp_after_second <= hp_after_first


def test_long_rest_fully_restores_hp_and_resources():
    party = [_fighter(max_hp=10, resources=[
        {"name": "Action Surge", "max": 1, "avg_value": 20, "regen": "short", "damage_type": "weapon", "magical": False},
    ])]
    bestiary = [_goblin()]
    items = [
        _encounter([{"bestiary_id": "g1", "count": 1}], item_id="e1",
                    spends={"f1": {"Action Surge": 1}}),
        {"type": "rest", "id": "r1", "rest_type": "long"},
        _encounter([{"bestiary_id": "g1", "count": 1}], item_id="e2"),
    ]
    result = simulate_day(party, bestiary, items)
    snaps = result["snapshots"]
    assert snaps[0]["resources_before"]["f1"]["Action Surge"] == 1
    assert snaps[1] is None  # the rest itself has no snapshot
    # after a long rest, the resource is back to full for the next encounter
    assert snaps[2]["resources_before"]["f1"]["Action Surge"] == 1


def test_short_rest_only_restores_short_regen_resources():
    party = [_fighter(resources=[
        {"name": "Warlock Pact Slot", "max": 2, "avg_value": 20, "regen": "short", "damage_type": "force", "magical": True},
        {"name": "Wizard Slot", "max": 2, "avg_value": 20, "regen": "long", "damage_type": "force", "magical": True},
    ])]
    bestiary = [_goblin()]
    items = [
        _encounter([{"bestiary_id": "g1", "count": 1}], item_id="e1",
                    spends={"f1": {"Warlock Pact Slot": 2, "Wizard Slot": 2}}),
        {"type": "rest", "id": "r1", "rest_type": "short"},
        _encounter([{"bestiary_id": "g1", "count": 1}], item_id="e2"),
    ]
    result = simulate_day(party, bestiary, items)
    before_second = result["snapshots"][2]["resources_before"]["f1"]
    assert before_second["Warlock Pact Slot"] == 2  # short-rest resource: back to full
    assert before_second["Wizard Slot"] == 0  # long-rest-only resource: still spent


def test_short_rest_applies_healing_when_recorded():
    party = [_fighter(max_hp=50)]
    bestiary = [_goblin()]
    items = [
        _encounter([{"bestiary_id": "g1", "count": 1}], item_id="e1", hp_overrides={"f1": 10}),
        {"type": "rest", "id": "r1", "rest_type": "short", "heals": {"f1": 15}},
        _encounter([{"bestiary_id": "g1", "count": 1}], item_id="e2"),
    ]
    result = simulate_day(party, bestiary, items)
    assert result["snapshots"][2]["hp_before"]["f1"] == 25  # 10 + 15


def test_short_rest_healing_cannot_exceed_max_hp():
    party = [_fighter(max_hp=50)]
    bestiary = [_goblin()]
    items = [
        _encounter([{"bestiary_id": "g1", "count": 1}], item_id="e1", hp_overrides={"f1": 45}),
        {"type": "rest", "id": "r1", "rest_type": "short", "heals": {"f1": 999}},
        _encounter([{"bestiary_id": "g1", "count": 1}], item_id="e2"),
    ]
    result = simulate_day(party, bestiary, items)
    assert result["snapshots"][2]["hp_before"]["f1"] == 50


def test_short_rest_with_no_recorded_healing_leaves_hp_unchanged():
    party = [_fighter(max_hp=50)]
    bestiary = [_goblin()]
    items = [
        _encounter([{"bestiary_id": "g1", "count": 1}], item_id="e1", hp_overrides={"f1": 10}),
        {"type": "rest", "id": "r1", "rest_type": "short"},
        _encounter([{"bestiary_id": "g1", "count": 1}], item_id="e2"),
    ]
    result = simulate_day(party, bestiary, items)
    assert result["snapshots"][2]["hp_before"]["f1"] == 10


def test_monster_resistance_reduces_effective_party_damage():
    party = [_fighter()]  # deals slashing damage
    resistant_goblin = _goblin(resistances=[{"type": "slashing", "magical_only": False}])
    bestiary_normal = [_goblin()]
    bestiary_resistant = [resistant_goblin]
    items = [_encounter([{"bestiary_id": "g1", "count": 1}])]

    normal = simulate_day(party, bestiary_normal, items)["snapshots"][0]
    resisted = simulate_day(party, bestiary_resistant, items)["snapshots"][0]
    assert resisted["party_dpr_total"] == pytest.approx(normal["party_dpr_total"] * 0.5)


def test_character_resistance_reduces_their_incoming_damage_share():
    resistant_fighter = _fighter(resistances=[{"type": "slashing", "magical_only": False}])
    party = [_fighter(id="f2"), resistant_fighter]
    # a beefy monster so the fight runs the full assumed length, giving the
    # resistance enough rounds to produce a visible HP difference
    bestiary = [_goblin(max_hp=500)]
    items = [_encounter([{"bestiary_id": "g1", "count": 1}], rounds_assumed=5)]
    result = simulate_day(party, bestiary, items)
    snap = result["snapshots"][0]
    # the resistant fighter should end the encounter with more HP left than the non-resistant one
    assert snap["hp_after"]["f1"] > snap["hp_after"]["f2"]


def test_action_economy_warning_fires_for_lopsided_monster_counts():
    party = [_fighter()]
    bestiary = [_goblin()]
    items = [_encounter([{"bestiary_id": "g1", "count": 5}])]
    snap = simulate_day(party, bestiary, items)["snapshots"][0]
    assert any("action economy" in w.lower() for w in snap["warnings"])


def test_total_incoming_damage_does_not_grow_with_party_size():
    # Monsters only get to act once each per round - a party of 4 identical
    # characters shouldn't take 4x the damage a solo character would, they
    # should split one fixed pool of monster damage between them.
    bestiary = [_goblin()]
    solo = simulate_day([_fighter(id="solo")], bestiary, [_encounter([{"bestiary_id": "g1", "count": 5}])])["snapshots"][0]
    party_of_four = simulate_day(
        [_fighter(id=f"f{i}") for i in range(4)], bestiary, [_encounter([{"bestiary_id": "g1", "count": 5}])],
    )["snapshots"][0]
    assert solo["monster_dpr_total"] == pytest.approx(party_of_four["monster_dpr_total"])


def test_total_incoming_damage_is_split_across_the_party_not_duplicated():
    # Two identical characters should each take roughly half the fixed pool,
    # not the full pool each (which would double-count the monsters' output).
    party = [_fighter(id="f1"), _fighter(id="f2")]
    bestiary = [_goblin()]
    items = [_encounter([{"bestiary_id": "g1", "count": 5}])]
    snap = simulate_day(party, bestiary, items)["snapshots"][0]
    solo_snap = simulate_day([_fighter(id="f1")], bestiary, items)["snapshots"][0]
    assert snap["monster_dpr_total"] == pytest.approx(solo_snap["monster_dpr_total"])


def test_worse_ac_character_takes_a_bigger_share_of_the_fixed_damage_pool():
    tanky = _fighter(id="tank", ac=20)
    squishy = _fighter(id="squishy", ac=10)
    party = [tanky, squishy]
    bestiary = [_goblin()]
    items = [_encounter([{"bestiary_id": "g1", "count": 5}], rounds_assumed=1)]
    snap = simulate_day(party, bestiary, items)["snapshots"][0]
    tank_loss = tanky["max_hp"] - snap["hp_after"]["tank"]
    squishy_loss = squishy["max_hp"] - snap["hp_after"]["squishy"]
    assert squishy_loss > tank_loss


def test_legendary_monster_triggers_a_warning_note():
    party = [_fighter()]
    boss = _goblin(monster_id="boss", is_legendary=True, legendary_actions=[{
        "name": "Claw", "default_uses_per_encounter": 2, "to_hit": 8, "die_count": 1, "die_sides": 8,
        "flat_bonus": 4, "damage_type": "slashing", "magical": True,
    }])
    bestiary = [boss]
    items = [_encounter([{"bestiary_id": "boss", "count": 1}])]
    snap = simulate_day(party, bestiary, items)["snapshots"][0]
    assert any("legendary" in w.lower() for w in snap["warnings"])


def test_battle_master_superiority_dice_only_apply_when_spent():
    fighter = _fighter(subclass="Battle Master", resources=[
        {"name": "Superiority Dice", "max": 4, "avg_value": 8, "regen": "short",
         "damage_type": "weapon", "magical": False},
    ])
    bestiary = [_goblin(max_hp=200)]
    items = [_encounter([{"bestiary_id": "g1", "count": 1}], spends={"f1": {"Superiority Dice": 4}})]
    with_dice = simulate_day([fighter], bestiary, items)["snapshots"][0]

    fighter_no_spend = _fighter(subclass="Battle Master", resources=[
        {"name": "Superiority Dice", "max": 4, "avg_value": 8, "regen": "short",
         "damage_type": "weapon", "magical": False},
    ])
    no_dice = simulate_day([fighter_no_spend], bestiary, [_encounter([{"bestiary_id": "g1", "count": 1}])])["snapshots"][0]
    assert with_dice["party_dpr_total"] > no_dice["party_dpr_total"]


def _raging_fighter(**overrides):
    return _fighter(resources=[
        {"name": "Rage", "max": 3, "avg_value": 2, "regen": "long",
         "damage_type": "weapon", "magical": False, "timing": "ongoing"},
    ], **overrides)


def test_rage_applies_to_every_attack_not_diluted_by_round_count():
    # Spending 1 Rage should add its bonus to EVERY hit for the whole fight,
    # not get divided down as if it were a single one-shot burst - so the
    # party's DPR contribution from Rage must be identical whether the fight
    # is assumed to last 1 round or 5.
    bestiary = [_goblin(max_hp=99999)]
    short_fight = simulate_day(
        [_raging_fighter()], bestiary,
        [_encounter([{"bestiary_id": "g1", "count": 1}], rounds_assumed=1, spends={"f1": {"Rage": 1}})],
    )["snapshots"][0]
    long_fight = simulate_day(
        [_raging_fighter()], bestiary,
        [_encounter([{"bestiary_id": "g1", "count": 1}], rounds_assumed=5, spends={"f1": {"Rage": 1}})],
    )["snapshots"][0]
    assert short_fight["party_dpr_total"] == pytest.approx(long_fight["party_dpr_total"])


def test_rage_increases_dpr_by_the_bonus_times_every_attack():
    unraged = simulate_day([_raging_fighter()], [_goblin(max_hp=99999)], [_encounter([{"bestiary_id": "g1", "count": 1}])])["snapshots"][0]
    raged = simulate_day(
        [_raging_fighter()], [_goblin(max_hp=99999)],
        [_encounter([{"bestiary_id": "g1", "count": 1}], spends={"f1": {"Rage": 1}})],
    )["snapshots"][0]
    # +2 dmg on a hit, applied to both of this fighter's 2 attacks (num_attacks=2 by default),
    # each landing at their normal hit chance - a real per-hit bump, not a diluted fraction of it.
    assert raged["party_dpr_total"] > unraged["party_dpr_total"] + 1.0  # comfortably more than a diluted ~0.67 bump


def test_rage_still_spends_down_the_resource_pool():
    fighter = _raging_fighter()
    bestiary = [_goblin()]
    items = [
        _encounter([{"bestiary_id": "g1", "count": 1}], item_id="e1", spends={"f1": {"Rage": 1}}),
        _encounter([{"bestiary_id": "g1", "count": 1}], item_id="e2"),
    ]
    result = simulate_day([fighter], bestiary, items)
    assert result["snapshots"][0]["resources_before"]["f1"]["Rage"] == 3  # unspent going into e1
    assert result["snapshots"][1]["resources_before"]["f1"]["Rage"] == 2  # 1 spent in e1, not yet rested


def test_rage_marked_ongoing_in_the_class_template():
    from app.engine.classes_data import class_resource_templates
    resources = class_resource_templates("Barbarian", level=5)
    rage = next(r for r in resources if r["name"] == "Rage")
    assert rage["timing"] == "ongoing"


def _action_surge_fighter(**overrides):
    return _fighter(resources=[
        {"name": "Action Surge", "max": 1, "avg_value": 15, "regen": "short",
         "damage_type": "weapon", "magical": False, "timing": "burst"},
    ], **overrides)


def test_action_surge_increases_party_dpr():
    # Rounds are now self-computed (no manual "rounds_assumed" to force),
    # so make the monster's HP effectively unkillable within the solver's
    # bounds - both scenarios then converge to the same clamped round count,
    # keeping the comparison apples-to-apples without needing to force a
    # specific number.
    bestiary = [_goblin(max_hp=10_000_000, attacks=[])]
    items_no_surge = [_encounter([{"bestiary_id": "g1", "count": 1}])]
    items_surged = [_encounter([{"bestiary_id": "g1", "count": 1}], spends={"f1": {"Action Surge": 1}})]
    no_surge = simulate_day([_action_surge_fighter()], bestiary, items_no_surge)["snapshots"][0]
    surged = simulate_day([_action_surge_fighter()], bestiary, items_surged)["snapshots"][0]
    assert surged["party_dpr_total"] > no_surge["party_dpr_total"]
    assert surged["rounds_assumed"] == pytest.approx(no_surge["rounds_assumed"])  # same clamp, apples-to-apples


def test_action_surge_is_a_plain_burst_with_no_special_mechanic():
    # No auto-computed value - just an ordinary burst resource the DM sets
    # a number on, like any other.
    from app.engine.classes_data import class_resource_templates
    resources = class_resource_templates("Fighter", level=5)
    surge = next(r for r in resources if r["name"] == "Action Surge")
    assert "auto_source" not in surge
    assert surge["timing"] == "burst"


def test_sorcery_points_and_a_spell_slot_stack_freely_in_the_same_encounter():
    # No action-economy conflict is modeled - both are independent burst
    # resources, and spending both should simply add their damage together.
    wizard_like_sorcerer = {
        "id": "s1", "name": "Sorcerer", "cls": "Sorcerer", "level": 5, "ac": 12, "max_hp": 30,
        "attack_ability_mod": 3, "magic_weapon_bonus": 0, "flat_damage_bonus": 0,
        "num_attacks": 0, "weapon_die_count": 0, "weapon_die_sides": 6,
        "weapon_damage_type": "force", "attack_is_magical": True,
        "rider_dice_count": 0, "rider_die_sides": 6, "rider_damage_type": "force",
        "feats": {}, "is_caster": True, "use_cantrip": False, "cantrip_die_override": None,
        "resources": [
            {"name": "Sorcery Points", "max": 5, "avg_value": 10, "regen": "long",
             "damage_type": "force", "magical": True},
            {"name": "Wizard Lv3 Slots", "max": 2, "slot_level": 3, "avg_value": 24.5,
             "damage_type": "force", "magical": True, "spell_id": None, "regen": "long"},
        ],
        "resistances": [], "vulnerabilities": [], "immunities": [],
    }
    bestiary = [_goblin(max_hp=10_000_000, attacks=[])]
    neither = simulate_day([wizard_like_sorcerer], bestiary, [_encounter([{"bestiary_id": "g1", "count": 1}])])["snapshots"][0]
    both = simulate_day(
        [wizard_like_sorcerer], bestiary,
        [_encounter([{"bestiary_id": "g1", "count": 1}],
                     spends={"s1": {"Sorcery Points": 1, "Wizard Lv3 Slots": 1}})],
    )["snapshots"][0]
    # both bursts land in the same fight (rounds_assumed converges to the
    # same clamped value in both scenarios, since the monster is effectively
    # unkillable either way), so their contributions add directly once
    # divided by that shared round count.
    assert both["rounds_assumed"] == pytest.approx(neither["rounds_assumed"])
    assert both["party_dpr_total"] == pytest.approx(neither["party_dpr_total"] + (10 + 24.5) / both["rounds_assumed"])


def test_party_save_proficiency_reduces_damage_from_a_save_based_attack():
    # Two otherwise-identical fighters, except one is proficient in Dex saves.
    # A dragon's breath weapon (Dex save) should hurt the proficient one less.
    proficient = _fighter(id="f_dex", saving_throw_proficiencies=["dex"])
    non_proficient = _fighter(id="f_none", saving_throw_proficiencies=[])
    party = [proficient, non_proficient]
    dragon = _goblin(max_hp=99999, attacks=[], save_attacks=[{
        "name": "Breath Weapon", "dc": 15, "die_count": 10, "die_sides": 6, "save_ability": "dex",
        "flat_bonus": 0, "damage_type": "fire", "magical": True, "half_on_save": True,
    }])
    # Single round, so neither character's HP floors at 0 and masks the difference.
    items = [_encounter([{"bestiary_id": "g1", "count": 1}], rounds_assumed=1)]
    snap = simulate_day(party, [dragon], items)["snapshots"][0]
    assert snap["hp_after"]["f_dex"] > snap["hp_after"]["f_none"]


def test_monster_innate_spell_contributes_to_incoming_damage():
    caster = _goblin(attacks=[], spells=[{"spell_id": "fire_bolt", "default_uses_per_encounter": 1, "spell_attack_bonus": 6}])
    party = [_fighter()]
    items = [_encounter([{"bestiary_id": "g1", "count": 1}])]
    snap = simulate_day(party, [caster], items)["snapshots"][0]
    assert snap["monster_dpr_total"] > 0


def test_known_spell_computes_real_spell_damage_not_flat_average():
    # A Wizard with Fireball known should get Fireball's actual save-based
    # math when spending a 3rd-level slot, not the generic flat placeholder.
    wizard = {
        "id": "w1", "name": "Wizard", "cls": "Wizard", "subclass": "School of Evocation",
        "level": 5, "ac": 12, "max_hp": 27,
        "attack_ability_mod": 3, "magic_weapon_bonus": 0, "flat_damage_bonus": 0,
        "num_attacks": 0, "weapon_die_count": 0, "weapon_die_sides": 6,
        "weapon_damage_type": "force", "attack_is_magical": True,
        "rider_dice_count": 0, "rider_die_sides": 6, "rider_damage_type": "force",
        "feats": {}, "is_caster": True, "use_cantrip": False, "cantrip_die_override": None,
        "cantrip_id": None,
        "resources": [{
            "name": "Wizard Lv3 Slots", "max": 2, "slot_level": 3,
            "avg_value": 24.5, "damage_type": "force", "magical": True,
            "spell_id": "fireball", "regen": "long",
        }],
        "resistances": [], "vulnerabilities": [], "immunities": [],
    }
    items = [_encounter([{"bestiary_id": "g1", "count": 1}], rounds_assumed=3,
                         spends={"w1": {"Wizard Lv3 Slots": 2}})]

    resistant_bestiary = [_goblin(max_hp=500, resistances=[{"type": "fire", "magical_only": False}])]
    normal_bestiary = [_goblin(max_hp=500)]

    resisted = simulate_day([wizard], resistant_bestiary, items)["snapshots"][0]
    normal = simulate_day([wizard], normal_bestiary, items)["snapshots"][0]
    # the goblin resists fire, so Fireball's damage should be visibly lower -
    # a flat generic avg_value wouldn't know Fireball is fire damage at all.
    assert resisted["party_dpr_total"] < normal["party_dpr_total"]


def test_custom_spell_from_the_library_is_usable_exactly_like_a_built_in_spell():
    custom_spells = [{
        "id": "homebrew-blast", "name": "Homebrew Blast", "level": 3, "damage_type": "necrotic",
        "mode": "save", "save_ability": "con", "half_on_save": True, "base_avg": 30.0, "per_level_avg": 4.0,
    }]
    wizard = {
        "id": "w1", "name": "Wizard", "cls": "Wizard", "subclass": "School of Evocation",
        "level": 5, "ac": 12, "max_hp": 27,
        "attack_ability_mod": 3, "magic_weapon_bonus": 0, "flat_damage_bonus": 0,
        "num_attacks": 0, "weapon_die_count": 0, "weapon_die_sides": 6,
        "weapon_damage_type": "force", "attack_is_magical": True,
        "rider_dice_count": 0, "rider_die_sides": 6, "rider_damage_type": "force",
        "feats": {}, "is_caster": True, "use_cantrip": False, "cantrip_die_override": None,
        "cantrip_id": None,
        "resources": [{
            "name": "Wizard Lv3 Slots", "max": 2, "slot_level": 3,
            "avg_value": 24.5, "damage_type": "force", "magical": True,
            "spell_id": "homebrew-blast", "regen": "long",
        }],
        "resistances": [], "vulnerabilities": [], "immunities": [],
    }
    items = [_encounter([{"bestiary_id": "g1", "count": 1}], rounds_assumed=3,
                         spends={"w1": {"Wizard Lv3 Slots": 2}})]
    resistant = simulate_day([wizard], [_goblin(max_hp=500, resistances=[{"type": "necrotic", "magical_only": False}])],
                              items, custom_spells=custom_spells)["snapshots"][0]
    normal = simulate_day([wizard], [_goblin(max_hp=500)], items, custom_spells=custom_spells)["snapshots"][0]
    assert resistant["party_dpr_total"] < normal["party_dpr_total"]


def test_without_the_custom_spell_passed_in_it_falls_back_to_the_flat_placeholder():
    # Same character/resource as above, but the caller forgot to pass
    # custom_spells - the engine shouldn't crash, it should just treat the
    # unknown spell_id as unassigned and use the resource's flat avg_value.
    wizard = {
        "id": "w1", "name": "Wizard", "cls": "Wizard", "level": 5, "ac": 12, "max_hp": 27,
        "attack_ability_mod": 3, "magic_weapon_bonus": 0, "flat_damage_bonus": 0,
        "num_attacks": 0, "weapon_die_count": 0, "weapon_die_sides": 6,
        "weapon_damage_type": "force", "attack_is_magical": True,
        "rider_dice_count": 0, "rider_die_sides": 6, "rider_damage_type": "force",
        "feats": {}, "is_caster": True, "use_cantrip": False, "cantrip_die_override": None,
        "cantrip_id": None,
        "resources": [{
            "name": "Wizard Lv3 Slots", "max": 2, "slot_level": 3,
            "avg_value": 24.5, "damage_type": "force", "magical": True,
            "spell_id": "homebrew-blast", "regen": "long",
        }],
        "resistances": [], "vulnerabilities": [], "immunities": [],
    }
    items = [_encounter([{"bestiary_id": "g1", "count": 1}], rounds_assumed=3,
                         spends={"w1": {"Wizard Lv3 Slots": 2}})]
    snap = simulate_day([wizard], [_goblin(max_hp=500)], items)["snapshots"][0]
    assert snap["party_dpr_total"] > 0


def test_starting_hp_below_max_carries_into_the_first_encounter():
    party = [_fighter(max_hp=50)]
    bestiary = [_goblin(max_hp=99999, attacks=[])]  # deals no damage, isolates the starting-HP effect
    items = [_encounter([{"bestiary_id": "g1", "count": 1}])]
    fresh = simulate_day(party, bestiary, items)["snapshots"][0]
    worn_down = simulate_day(party, bestiary, items, starting_hp={"f1": 10})["snapshots"][0]
    assert fresh["hp_after"]["f1"] == 50
    assert worn_down["hp_after"]["f1"] == 10


def test_starting_resources_below_max_are_available_to_spend_in_the_first_encounter():
    fighter = _fighter(resources=[
        {"name": "Action Surge", "max": 1, "avg_value": 20, "regen": "short", "damage_type": "weapon", "magical": False},
    ])
    bestiary = [_goblin()]
    items = [_encounter([{"bestiary_id": "g1", "count": 1}])]
    result = simulate_day([fighter], bestiary, items, starting_resources={"f1": {"Action Surge": 0}})
    assert result["snapshots"][0]["resources_before"]["f1"]["Action Surge"] == 0


def test_hp_override_on_an_encounter_replaces_the_predicted_value_going_forward():
    party = [_fighter(max_hp=50)]
    bestiary = [_goblin()]
    items = [
        _encounter([{"bestiary_id": "g1", "count": 1}], item_id="e1", rounds_assumed=1,
                    hp_overrides={"f1": 12}),  # "actually they got hit way harder than expected"
        _encounter([{"bestiary_id": "g1", "count": 1}], item_id="e2"),
    ]
    result = simulate_day(party, bestiary, items)
    first, second = result["snapshots"]
    assert first["hp_after"]["f1"] == 12
    assert first["predicted_hp_after"]["f1"] != 12  # the prediction itself is untouched, just overridden
    # the second encounter's damage math starts from the overridden 12 HP, not the predicted value
    assert second["hp_after"]["f1"] <= 12


def test_no_hp_override_means_predicted_and_actual_hp_after_match():
    party = [_fighter(max_hp=50)]
    bestiary = [_goblin()]
    items = [_encounter([{"bestiary_id": "g1", "count": 1}])]
    snap = simulate_day(party, bestiary, items)["snapshots"][0]
    assert snap["hp_after"]["f1"] == snap["predicted_hp_after"]["f1"]


def test_hp_before_reflects_the_actual_carried_forward_value_not_just_max_hp():
    party = [_fighter(max_hp=50)]
    bestiary = [_goblin()]
    items = [
        _encounter([{"bestiary_id": "g1", "count": 1}], item_id="e1", hp_overrides={"f1": 7}),
        _encounter([{"bestiary_id": "g1", "count": 1}], item_id="e2"),
    ]
    result = simulate_day(party, bestiary, items)
    assert result["snapshots"][0]["hp_before"]["f1"] == 50
    assert result["snapshots"][1]["hp_before"]["f1"] == 7


def _cantrip_wizard(**overrides):
    ch = {
        "id": "w1", "name": "Wizard", "cls": "Wizard", "level": 5, "ac": 12, "max_hp": 30,
        "attack_ability_mod": 3, "magic_weapon_bonus": 0, "flat_damage_bonus": 0,
        "num_attacks": 0, "weapon_die_count": 0, "weapon_die_sides": 6,
        "weapon_damage_type": "fire", "attack_is_magical": True,
        "rider_dice_count": 0, "rider_die_sides": 6, "rider_damage_type": "fire",
        "feats": {}, "is_caster": True, "use_cantrip": True, "cantrip_die_override": 11.0, "cantrip_id": None,
        "resources": [], "resistances": [], "vulnerabilities": [], "immunities": [],
    }
    ch.update(overrides)
    return ch


def test_displacing_spell_slot_reduces_at_will_contribution_proportionally():
    # Casting a leveled spell uses the same action a cantrip would have, so
    # it should NOT simply stack a full turn of cantrip damage plus the
    # spell's damage - one round's worth of cantrip gets displaced instead.
    wizard = _cantrip_wizard(resources=[
        {"name": "Wizard Lv3 Slots", "max": 2, "slot_level": 3, "avg_value": 28.0,
         "damage_type": "fire", "magical": True, "spell_id": None, "regen": "long",
         "displaces_at_will": True},
    ])
    bestiary = [_goblin(max_hp=10_000_000, attacks=[])]
    no_spell = simulate_day([wizard], bestiary, [_encounter([{"bestiary_id": "g1", "count": 1}])])["snapshots"][0]
    one_spell = simulate_day(
        [wizard], bestiary,
        [_encounter([{"bestiary_id": "g1", "count": 1}], spends={"w1": {"Wizard Lv3 Slots": 1}})],
    )["snapshots"][0]
    at_will = no_spell["party_dpr_total"]
    r = one_spell["rounds_assumed"]
    assert one_spell["rounds_assumed"] == pytest.approx(no_spell["rounds_assumed"])
    # (r-1) cantrip-rounds + 1 fireball-round, averaged over r rounds - not
    # r cantrip-rounds PLUS a fireball on top, which would double-count.
    expected = (at_will * (r - 1) + 28.0) / r
    assert one_spell["party_dpr_total"] == pytest.approx(expected)


def test_non_displacing_burst_still_stacks_on_top_of_at_will():
    # Divine Smite / Superiority Dice trigger on an attack the character is
    # already making, so they should NOT reduce the at-will contribution -
    # this is a regression check that the displacement fix didn't break them.
    fighter = _fighter(resources=[
        {"name": "Superiority Dice", "max": 4, "avg_value": 8, "regen": "short",
         "damage_type": "weapon", "magical": False},  # timing defaults to "burst", no displaces_at_will
    ])
    bestiary = [_goblin(max_hp=10_000_000, attacks=[])]
    no_dice = simulate_day([fighter], bestiary, [_encounter([{"bestiary_id": "g1", "count": 1}])])["snapshots"][0]
    with_dice = simulate_day(
        [fighter], bestiary,
        [_encounter([{"bestiary_id": "g1", "count": 1}], spends={"f1": {"Superiority Dice": 1}})],
    )["snapshots"][0]
    assert with_dice["rounds_assumed"] == pytest.approx(no_dice["rounds_assumed"])
    assert with_dice["party_dpr_total"] == pytest.approx(no_dice["party_dpr_total"] + 8 / with_dice["rounds_assumed"])


def test_warning_fires_when_more_spells_cast_than_rounds_assumed():
    wizard = _cantrip_wizard(resources=[
        {"name": "Wizard Lv3 Slots", "max": 4, "slot_level": 3, "avg_value": 28.0,
         "damage_type": "fire", "magical": True, "spell_id": None, "regen": "long",
         "displaces_at_will": True},
    ])
    bestiary = [_goblin()]
    items = [_encounter([{"bestiary_id": "g1", "count": 1}], rounds_assumed=2, spends={"w1": {"Wizard Lv3 Slots": 4}})]
    snap = simulate_day([wizard], bestiary, items)["snapshots"][0]
    assert any("more spell-slot casts" in w for w in snap["warnings"])


def test_spell_slot_templates_default_to_displacing_at_will():
    from app.engine.classes_data import class_resource_templates
    resources = class_resource_templates("Wizard", level=5)
    lv3 = next(r for r in resources if r["name"] == "Wizard Lv3 Slots")
    assert lv3["displaces_at_will"] is True


def test_warlock_pact_slots_default_to_displacing_at_will():
    from app.engine.classes_data import class_resource_templates
    resources = class_resource_templates("Warlock", level=5)
    pact = next(r for r in resources if "Pact Slots" in r["name"])
    assert pact["displaces_at_will"] is True


def test_superiority_dice_do_not_displace_at_will_by_default():
    from app.engine.classes_data import class_resource_templates
    resources = class_resource_templates("Fighter", level=5, subclass="Battle Master")
    dice = next(r for r in resources if r["name"] == "Superiority Dice")
    assert not dice.get("displaces_at_will")


def _fireball_wizard(**overrides):
    ch = {
        "id": "w1", "name": "Wizard", "cls": "Wizard", "level": 5, "ac": 12, "max_hp": 30,
        "attack_ability_mod": 3, "magic_weapon_bonus": 0, "flat_damage_bonus": 0,
        "num_attacks": 0, "weapon_die_count": 0, "weapon_die_sides": 6,
        "weapon_damage_type": "fire", "attack_is_magical": True,
        "rider_dice_count": 0, "rider_die_sides": 6, "rider_damage_type": "fire",
        "feats": {}, "is_caster": True, "use_cantrip": False, "cantrip_die_override": None, "cantrip_id": None,
        "resources": [{"name": "Wizard Lv3 Slots", "max": 2, "slot_level": 3, "avg_value": 28.0,
                        "damage_type": "fire", "magical": True, "spell_id": "fireball", "regen": "long",
                        "displaces_at_will": False}],
        "resistances": [], "vulnerabilities": [], "immunities": [],
    }
    ch.update(overrides)
    return ch


def test_aoe_spell_deals_more_total_damage_against_a_crowd_than_a_single_target():
    wizard = _fireball_wizard()
    items = [_encounter([{"bestiary_id": "g1", "count": 1}], rounds_assumed=1, spends={"w1": {"Wizard Lv3 Slots": 1}})]
    solo = simulate_day([wizard], [_goblin()], items)["snapshots"][0]

    items5 = [_encounter([{"bestiary_id": "g1", "count": 5}], rounds_assumed=1, spends={"w1": {"Wizard Lv3 Slots": 1}})]
    crowd = simulate_day([wizard], [_goblin()], items5)["snapshots"][0]
    assert crowd["party_dpr_total"] > solo["party_dpr_total"]


def test_aoe_spell_is_capped_and_does_not_scale_with_unlimited_monster_count():
    # Fireball realistically doesn't catch every single enemy in a huge
    # horde - its damage multiplier should stop growing past its own
    # aoe_targets ceiling (3), not keep climbing forever.
    wizard = _fireball_wizard()
    bestiary = [_goblin(max_hp=10_000_000, attacks=[])]
    items5 = [_encounter([{"bestiary_id": "g1", "count": 5}], spends={"w1": {"Wizard Lv3 Slots": 1}})]
    items10 = [_encounter([{"bestiary_id": "g1", "count": 10}], spends={"w1": {"Wizard Lv3 Slots": 1}})]
    five = simulate_day([wizard], bestiary, items5)["snapshots"][0]
    ten = simulate_day([wizard], bestiary, items10)["snapshots"][0]
    assert five["rounds_assumed"] == pytest.approx(ten["rounds_assumed"])
    assert five["party_dpr_total"] == pytest.approx(ten["party_dpr_total"])


def test_monster_innate_aoe_spell_is_capped_by_party_size():
    caster_goblin = _goblin(max_hp=10_000_000, attacks=[], spells=[
        {"spell_id": "fireball", "default_uses_per_encounter": 1, "spell_save_dc": 15},
    ])
    solo_party = [_fighter(id="f1", max_hp=10_000_000)]
    big_party = [_fighter(id=f"f{i}", max_hp=10_000_000) for i in range(6)]
    items = [_encounter([{"bestiary_id": "g1", "count": 1}])]
    solo_snap = simulate_day(solo_party, [caster_goblin], items)["snapshots"][0]
    big_snap = simulate_day(big_party, [caster_goblin], items)["snapshots"][0]
    assert solo_snap["rounds_assumed"] == pytest.approx(big_snap["rounds_assumed"])
    # 1 target for the solo party vs. capped at 3 (Fireball's aoe_targets) for
    # a 6-person party - total monster DPR output should grow with the AoE
    # hitting more people, but not linearly with party size past the cap.
    assert big_snap["monster_dpr_total"] > solo_snap["monster_dpr_total"]
    assert big_snap["monster_dpr_total"] == pytest.approx(solo_snap["monster_dpr_total"] * 3)


def test_bonus_action_spells_are_flagged_in_the_spell_data():
    from app.engine.spells import SPELLS
    assert SPELLS["spiritual_weapon"]["bonus_action"] is True
    assert SPELLS["hail_of_thorns"]["bonus_action"] is True
    assert not SPELLS["fireball"].get("bonus_action")


def test_encounter_level_monster_uses_override_flows_through_simulate_day():
    # This is the actual end-to-end path the DM edits: item.monster_uses,
    # keyed by bestiary_id then ability name, set per-encounter rather than
    # baked into the monster's stat block.
    boss = _goblin(monster_id="boss", max_hp=99999, attacks=[], is_legendary=True, legendary_actions=[{
        "name": "Tail Attack", "default_uses_per_encounter": 3, "to_hit": 10,
        "die_count": 2, "die_sides": 8, "flat_bonus": 6, "damage_type": "bludgeoning", "magical": True,
    }])
    party = [_fighter(max_hp=999999)]
    items_default = [_encounter([{"bestiary_id": "boss", "count": 1}], rounds_assumed=1)]
    items_override = [_encounter([{"bestiary_id": "boss", "count": 1}], rounds_assumed=1,
                                   monster_uses={"boss": {"Tail Attack (legendary)": 1}})]
    default_snap = simulate_day(party, [boss], items_default)["snapshots"][0]
    override_snap = simulate_day(party, [boss], items_override)["snapshots"][0]
    # "if you expect the boss to use it once in an encounter, it should only be added once"
    assert override_snap["monster_dpr_total"] == pytest.approx(default_snap["monster_dpr_total"] / 3)


def test_monster_uses_override_does_not_affect_other_encounters_in_the_day():
    boss = _goblin(monster_id="boss", max_hp=99999, attacks=[], is_legendary=True, legendary_actions=[{
        "name": "Tail Attack", "default_uses_per_encounter": 3, "to_hit": 10,
        "die_count": 2, "die_sides": 8, "flat_bonus": 6, "damage_type": "bludgeoning", "magical": True,
    }])
    party = [_fighter(max_hp=999999)]
    items = [
        _encounter([{"bestiary_id": "boss", "count": 1}], item_id="e1", rounds_assumed=1,
                    monster_uses={"boss": {"Tail Attack (legendary)": 1}}),
        _encounter([{"bestiary_id": "boss", "count": 1}], item_id="e2", rounds_assumed=1),
    ]
    result = simulate_day(party, [boss], items)
    # e2 has no override of its own - it should fall back to the bestiary's
    # own default (3), not inherit e1's override (1).
    assert result["snapshots"][1]["monster_dpr_total"] == pytest.approx(result["snapshots"][0]["monster_dpr_total"] * 3)


# ---- Legendary Resistance: converts failed saves into successes ----

def _fireball_wizard_lr(**overrides):
    ch = {
        "id": "w1", "name": "Wizard", "cls": "Wizard", "level": 5, "ac": 12, "max_hp": 30,
        "attack_ability_mod": 3, "magic_weapon_bonus": 0, "flat_damage_bonus": 0,
        "num_attacks": 0, "weapon_die_count": 0, "weapon_die_sides": 6,
        "weapon_damage_type": "fire", "attack_is_magical": True,
        "rider_dice_count": 0, "rider_die_sides": 6, "rider_damage_type": "fire",
        "feats": {}, "is_caster": True, "use_cantrip": False, "cantrip_die_override": None, "cantrip_id": None,
        "resources": [{"name": "Wizard Lv3 Slots", "max": 3, "slot_level": 3, "avg_value": 28.0,
                        "damage_type": "fire", "magical": True, "spell_id": "fireball", "regen": "long",
                        "displaces_at_will": False}],
        "resistances": [], "vulnerabilities": [], "immunities": [],
    }
    ch.update(overrides)
    return ch


def _legendary_dragon(legendary_resistances=0, **overrides):
    dragon = {"id": "d1", "name": "Dragon", "ac": 19, "max_hp": 999999, "xp": 10000, "save_bonuses": {"dex": 3},
              "is_legendary": True, "legendary_resistances": legendary_resistances,
              "attacks": [], "save_attacks": [], "legendary_actions": [], "spells": [],
              "resistances": [], "vulnerabilities": [], "immunities": []}
    dragon.update(overrides)
    return dragon


def test_legendary_resistance_reduces_save_based_damage_taken():
    wizard = _fireball_wizard_lr()
    items = [_encounter([{"bestiary_id": "d1", "count": 1}], spends={"w1": {"Wizard Lv3 Slots": 3}})]
    no_lr = simulate_day([wizard], [_legendary_dragon(0)], items)["snapshots"][0]
    with_lr = simulate_day([wizard], [_legendary_dragon(3)], items)["snapshots"][0]
    assert with_lr["party_dpr_total"] < no_lr["party_dpr_total"]


def test_legendary_resistance_full_coverage_forces_the_half_on_save_outcome():
    # 3 resistances covering exactly 3 casts of a spell with half_on_save
    # should mean every cast lands as if it had succeeded its save - i.e.
    # exactly the half-damage outcome, every time, not the normal blend.
    wizard = _fireball_wizard_lr()
    items = [_encounter([{"bestiary_id": "d1", "count": 1}], spends={"w1": {"Wizard Lv3 Slots": 3}})]
    with_lr = simulate_day([wizard], [_legendary_dragon(3)], items)["snapshots"][0]
    guaranteed_half = 28.0 * 0.5  # Fireball's base_avg at slot level 3, halved
    expected_total_over_3_casts = 3 * guaranteed_half
    # party_dpr_total = expected_total / rounds_assumed; recover the total from that
    assert with_lr["party_dpr_total"] * with_lr["rounds_assumed"] == pytest.approx(expected_total_over_3_casts)


def test_legendary_resistance_caps_at_the_number_of_actual_save_based_casts():
    # 10 resistances against only 3 casts shouldn't do anything MORE than
    # full coverage - a boss can't "extra resist" casts that never happened.
    wizard = _fireball_wizard_lr()
    items = [_encounter([{"bestiary_id": "d1", "count": 1}], spends={"w1": {"Wizard Lv3 Slots": 3}})]
    full_coverage = simulate_day([wizard], [_legendary_dragon(3)], items)["snapshots"][0]
    excess = simulate_day([wizard], [_legendary_dragon(10)], items)["snapshots"][0]
    assert excess["party_dpr_total"] == pytest.approx(full_coverage["party_dpr_total"])


def test_legendary_resistance_does_nothing_for_a_non_legendary_monster():
    wizard = _fireball_wizard_lr()
    items = [_encounter([{"bestiary_id": "d1", "count": 1}], spends={"w1": {"Wizard Lv3 Slots": 3}})]
    # legendary_resistances set but is_legendary is False - shouldn't apply.
    non_legendary_with_lr_field = _legendary_dragon(3, is_legendary=False)
    non_legendary_no_lr = _legendary_dragon(0, is_legendary=False)
    a = simulate_day([wizard], [non_legendary_with_lr_field], items)["snapshots"][0]
    b = simulate_day([wizard], [non_legendary_no_lr], items)["snapshots"][0]
    assert a["party_dpr_total"] == pytest.approx(b["party_dpr_total"])


def test_legendary_resistance_does_not_affect_spell_attack_rolls():
    # Legendary Resistance only converts failed SAVES - it has no bearing
    # on an attack-roll spell (there's no save to turn into a success).
    attack_mode_wizard = _fireball_wizard_lr(resources=[
        {"name": "Wizard Lv3 Slots", "max": 3, "slot_level": 3, "avg_value": 28.0,
         "damage_type": "fire", "magical": True, "spell_id": "scorching_ray", "regen": "long",
         "displaces_at_will": False},
    ])
    items = [_encounter([{"bestiary_id": "d1", "count": 1}], spends={"w1": {"Wizard Lv3 Slots": 3}})]
    no_lr = simulate_day([attack_mode_wizard], [_legendary_dragon(0)], items)["snapshots"][0]
    with_lr = simulate_day([attack_mode_wizard], [_legendary_dragon(3)], items)["snapshots"][0]
    assert with_lr["party_dpr_total"] == pytest.approx(no_lr["party_dpr_total"])


def test_legendary_resistance_does_not_reduce_at_will_or_ongoing_damage():
    # Only save-based spell casts are eligible - a boss can't legendary-
    # resist its way out of just getting hit by a sword.
    fighter = _fighter()
    wizard = _fireball_wizard_lr()
    items = [_encounter([{"bestiary_id": "d1", "count": 1}], spends={"w1": {"Wizard Lv3 Slots": 3}})]
    no_lr = simulate_day([fighter, wizard], [_legendary_dragon(0)], items)["snapshots"][0]
    with_lr = simulate_day([fighter, wizard], [_legendary_dragon(3)], items)["snapshots"][0]
    # The fighter's own at-will contribution should be identical either way.
    reduction = no_lr["party_dpr_total"] - with_lr["party_dpr_total"]
    assert reduction > 0
    assert reduction < no_lr["party_dpr_total"]  # didn't wipe out the fighter's share too
