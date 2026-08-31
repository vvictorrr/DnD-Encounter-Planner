"""Reference-data endpoints.

These exist so the frontend never has to duplicate game knowledge (class
lists, subclasses, feats, spells, spell-slot progressions, CR seed numbers)
- the backend is the single source of truth, and the frontend just renders
whatever it's handed.
"""
from flask import jsonify, request

from ..engine import (
    ABILITIES,
    CASTING_ABILITY,
    CLASS_LIST,
    CR_ORDER,
    CR_SEED,
    DAMAGE_TYPES,
    FEATS,
    OPTIMIZER_CALIBRATION,
    SAVE_PROFICIENCIES,
    SPELLS,
    SUBCLASSES,
    class_resource_templates,
    seed_monster_from_cr,
    suggested_rider,
)
from . import api_bp


@api_bp.get("/reference-data")
def reference_data():
    return jsonify({
        "damage_types": DAMAGE_TYPES,
        "class_list": CLASS_LIST,
        "subclasses": SUBCLASSES,
        "feats": FEATS,
        "cr_order": CR_ORDER,
        "optimizer_calibration": OPTIMIZER_CALIBRATION,
        "spells": SPELLS,
        "abilities": ABILITIES,
        "save_proficiencies": SAVE_PROFICIENCIES,
        "casting_ability": CASTING_ABILITY,
    })


@api_bp.post("/reference/resource-template")
def resource_template():
    """Auto-fill a class/level/subclass's default resource pools.

    Spell-slot resources always come back with ``spell_id: null`` - which
    spell fills a slot is a manual choice made per-resource in the Party
    editor (a dropdown right on that resource), not something this endpoint
    guesses at.
    """
    body = request.get_json(silent=True) or {}
    cls, level, subclass = body.get("cls"), body.get("level"), body.get("subclass")
    if cls not in CLASS_LIST or not isinstance(level, int) or not (1 <= level <= 20):
        return jsonify({"error": "cls must be a known class and level must be an int 1-20"}), 400
    return jsonify({
        "resources": class_resource_templates(cls, level, subclass),
        # An always-on rider effect (Sneak Attack, ...) to auto-fill on the
        # character sheet, or null if this class doesn't have one - these
        # are NOT limited resources, so they're returned separately.
        "rider_suggestion": suggested_rider(cls, level),
    })


@api_bp.post("/reference/monster-seed")
def monster_seed():
    body = request.get_json(silent=True) or {}
    cr = body.get("cr")
    if cr not in CR_SEED:
        return jsonify({"error": f"cr must be one of {CR_ORDER}"}), 400
    return jsonify({"seed": seed_monster_from_cr(cr)})

