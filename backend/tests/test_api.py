def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_root_serves_something_reasonable_even_without_a_built_frontend(client):
    # In CI/test environments the frontend usually isn't built - the app
    # should still respond helpfully instead of crashing.
    resp = client.get("/")
    assert resp.status_code == 200


def test_unmatched_api_route_is_a_404_not_the_spa_fallback(client):
    resp = client.get("/api/this-route-does-not-exist")
    assert resp.status_code == 404


def test_reference_data_exposes_game_constants(client):
    resp = client.get("/api/reference-data")
    assert resp.status_code == 200
    body = resp.get_json()
    assert "fire" in body["damage_types"]
    assert "Fighter" in body["class_list"]
    assert "gwm" in body["feats"]
    assert "Battle Master" in body["subclasses"]["Fighter"]
    assert "fireball" in body["spells"]


def test_resource_template_for_a_known_class(client):
    resp = client.post("/api/reference/resource-template", json={"cls": "Barbarian", "level": 5})
    assert resp.status_code == 200
    resources = resp.get_json()["resources"]
    assert any(r["name"] == "Rage" for r in resources)


def test_resource_template_respects_subclass_gating(client):
    battle_master = client.post("/api/reference/resource-template",
                                  json={"cls": "Fighter", "level": 5, "subclass": "Battle Master"}).get_json()
    champion = client.post("/api/reference/resource-template",
                             json={"cls": "Fighter", "level": 5, "subclass": "Champion"}).get_json()
    assert any(r["name"] == "Superiority Dice" for r in battle_master["resources"])
    assert not any(r["name"] == "Superiority Dice" for r in champion["resources"])


def test_resource_template_rejects_unknown_class(client):
    resp = client.post("/api/reference/resource-template", json={"cls": "Necromancer", "level": 5})
    assert resp.status_code == 400


def test_resource_template_spell_slots_always_come_back_unassigned(client):
    # Which spell fills a slot is chosen manually per-resource in the UI now,
    # not auto-picked by this endpoint - every slot should be empty.
    resp = client.post("/api/reference/resource-template", json={"cls": "Wizard", "level": 5})
    assert resp.status_code == 200
    lv3 = next(r for r in resp.get_json()["resources"] if r["name"] == "Wizard Lv3 Slots")
    assert lv3["spell_id"] is None
    assert lv3["slot_level"] == 3


def test_monster_seed_for_a_known_cr(client):
    resp = client.post("/api/reference/monster-seed", json={"cr": "5"})
    assert resp.status_code == 200
    seed = resp.get_json()["seed"]
    assert seed["max_hp"] > 0
    assert len(seed["attacks"]) == 1


def test_monster_seed_rejects_unknown_cr(client):
    resp = client.post("/api/reference/monster-seed", json={"cr": "not-a-cr"})
    assert resp.status_code == 400


def test_campaign_crud_round_trip(client):
    create = client.post("/api/campaigns", json={"name": "Test Campaign", "party": [], "bestiary": [], "day_plan": []})
    assert create.status_code == 201
    campaign_id = create.get_json()["id"]

    listing = client.get("/api/campaigns")
    assert listing.status_code == 200
    assert any(c["id"] == campaign_id for c in listing.get_json())

    fetched = client.get(f"/api/campaigns/{campaign_id}")
    assert fetched.status_code == 200
    assert fetched.get_json()["name"] == "Test Campaign"

    updated = client.put(f"/api/campaigns/{campaign_id}", json={"name": "Renamed Campaign"})
    assert updated.status_code == 200
    assert updated.get_json()["name"] == "Renamed Campaign"

    deleted = client.delete(f"/api/campaigns/{campaign_id}")
    assert deleted.status_code == 204

    gone = client.get(f"/api/campaigns/{campaign_id}")
    assert gone.status_code == 404


def test_get_missing_campaign_is_404(client):
    resp = client.get("/api/campaigns/999999")
    assert resp.status_code == 404


def test_simulate_endpoint_runs_the_engine(client, sample_character, sample_monster):
    payload = {
        "party": [sample_character],
        "bestiary": [sample_monster],
        "items": [{
            "type": "encounter", "id": "e1", "name": "Test Fight", "rounds_assumed": 3,
            "monsters": [{"bestiary_id": sample_monster["id"], "count": 1}], "spends": {},
        }],
    }
    resp = client.post("/api/simulate", json=payload)
    assert resp.status_code == 200
    snapshots = resp.get_json()["snapshots"]
    assert len(snapshots) == 1
    assert "rounds_to_kill_monsters" in snapshots[0]


def test_simulate_endpoint_rejects_non_array_fields(client):
    resp = client.post("/api/simulate", json={"party": "not-a-list", "bestiary": [], "items": []})
    assert resp.status_code == 400


def test_simulate_endpoint_accepts_starting_hp_and_custom_spells(client, sample_character, sample_monster):
    payload = {
        "party": [sample_character],
        "bestiary": [sample_monster],
        "items": [{
            "type": "encounter", "id": "e1", "name": "Test Fight", "rounds_assumed": 3,
            "monsters": [{"bestiary_id": sample_monster["id"], "count": 1}], "spends": {},
        }],
        "starting_hp": {sample_character["id"]: 5},
        "custom_spells": [{"id": "homebrew", "name": "Homebrew", "level": 1, "damage_type": "force",
                            "mode": "attack", "base_avg": 5.0, "per_level_avg": 1.0}],
    }
    resp = client.post("/api/simulate", json=payload)
    assert resp.status_code == 200
    snap = resp.get_json()["snapshots"][0]
    # starting HP of 5 should cap what's left after this fight at or below 5
    assert snap["hp_after"][sample_character["id"]] <= 5


def test_simulate_endpoint_returns_400_not_500_on_malformed_character(client, sample_monster):
    payload = {
        "party": [{"id": "broken", "name": "Missing Fields"}],  # missing required keys on purpose
        "bestiary": [sample_monster],
        "items": [{"type": "encounter", "id": "e1", "name": "Test", "rounds_assumed": 3,
                   "monsters": [{"bestiary_id": sample_monster["id"], "count": 1}], "spends": {}}],
    }
    resp = client.post("/api/simulate", json=payload)
    assert resp.status_code == 400
