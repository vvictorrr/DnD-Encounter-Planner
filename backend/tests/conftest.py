import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db as _db


@pytest.fixture()
def app():
    application = create_app(TestConfig)
    with application.app_context():
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def sample_character():
    return {
        "id": "hero-1", "name": "Test Fighter", "cls": "Fighter", "subclass": "Champion", "level": 5,
        "ac": 16, "max_hp": 45,
        "ability_scores": {"str": 18, "dex": 12, "con": 16, "int": 10, "wis": 12, "cha": 8},
        "saving_throw_proficiencies": ["str", "con"],
        "attack_ability_mod": 4, "magic_weapon_bonus": 1, "flat_damage_bonus": 4,
        "num_attacks": 2, "weapon_die_count": 2, "weapon_die_sides": 6,
        "weapon_damage_type": "slashing", "attack_is_magical": True,
        "rider_dice_count": 0, "rider_die_sides": 6, "rider_damage_type": "slashing",
        "feats": {"gwm": False, "ss": False, "pam": False, "cbe": False,
                   "savage": False, "dueling_style": False, "archery_style": False},
        "is_caster": False, "use_cantrip": False, "cantrip_die_override": None,
        "cantrip_id": None, "spell_attack_bonus": None, "spell_save_dc": None,
        "resources": [], "resistances": [], "vulnerabilities": [], "immunities": [],
    }


@pytest.fixture()
def sample_monster():
    return {
        "id": "goblin-1", "name": "Test Goblin", "ac": 15, "max_hp": 20, "xp": 50,
        "save_bonuses": {"str": 0, "dex": 2, "con": 1, "int": -1, "wis": 0, "cha": -1},
        "is_legendary": False,
        "attacks": [{
            "name": "Scimitar", "count": 1, "to_hit": 4, "die_count": 1, "die_sides": 6,
            "flat_bonus": 2, "damage_type": "slashing", "magical": False,
        }],
        "save_attacks": [], "legendary_actions": [], "legendary_resistances": 0,
        "spells": [], "resistances": [], "vulnerabilities": [], "immunities": [],
    }
