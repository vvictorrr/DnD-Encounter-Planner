from flask import jsonify, request

from ..engine import simulate_day
from . import api_bp


@api_bp.post("/simulate")
def simulate():
    """Run a full adventuring day and return per-encounter results.

    Expects ``{"party": [...], "bestiary": [...], "items": [...]}`` using the
    snake_case shapes documented in ``docs/schema.md``, plus optionally
    ``"custom_spells": [...]`` (the campaign's Spell Library),
    ``"starting_hp": {char_id: hp}``, and ``"starting_resources":
    {char_id: {resource_name: count}}`` for a day that doesn't start at
    full health/resources. This endpoint is stateless - it doesn't read or
    write the database, so it can be called freely while a campaign is
    being edited, before the user decides to save.
    """
    body = request.get_json(silent=True) or {}
    party = body.get("party", [])
    bestiary = body.get("bestiary", [])
    items = body.get("items", [])
    custom_spells = body.get("custom_spells", [])
    starting_hp = body.get("starting_hp", {})
    starting_resources = body.get("starting_resources", {})

    if not isinstance(party, list) or not isinstance(bestiary, list) or not isinstance(items, list):
        return jsonify({"error": "party, bestiary, and items must all be arrays"}), 400

    try:
        result = simulate_day(
            party, bestiary, items, custom_spells=custom_spells,
            starting_hp=starting_hp, starting_resources=starting_resources,
        )
    except KeyError as exc:
        return jsonify({"error": f"missing required field: {exc}"}), 400
    except (TypeError, ZeroDivisionError) as exc:
        return jsonify({"error": f"invalid input: {exc}"}), 400

    return jsonify(result)
