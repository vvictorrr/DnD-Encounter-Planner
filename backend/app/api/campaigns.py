from flask import jsonify, request

from ..extensions import db
from ..models import Campaign
from . import api_bp


@api_bp.get("/campaigns")
def list_campaigns():
    """Lightweight list for a picker UI - full party/bestiary/day_plan omitted."""
    campaigns = Campaign.query.order_by(Campaign.updated_at.desc()).all()
    return jsonify([
        {"id": c.id, "name": c.name, "updated_at": c.updated_at.isoformat()}
        for c in campaigns
    ])


@api_bp.post("/campaigns")
def create_campaign():
    body = request.get_json(silent=True) or {}
    campaign = Campaign(
        name=body.get("name", "Untitled Campaign"),
        party=body.get("party", []),
        bestiary=body.get("bestiary", []),
        day_plan=body.get("day_plan", []),
        custom_spells=body.get("custom_spells", []),
        starting_hp=body.get("starting_hp", {}),
        starting_resources=body.get("starting_resources", {}),
    )
    db.session.add(campaign)
    db.session.commit()
    return jsonify(campaign.to_dict()), 201


@api_bp.get("/campaigns/<int:campaign_id>")
def get_campaign(campaign_id: int):
    campaign = db.session.get(Campaign, campaign_id)
    if not campaign:
        return jsonify({"error": "campaign not found"}), 404
    return jsonify(campaign.to_dict())


@api_bp.put("/campaigns/<int:campaign_id>")
def update_campaign(campaign_id: int):
    campaign = db.session.get(Campaign, campaign_id)
    if not campaign:
        return jsonify({"error": "campaign not found"}), 404
    body = request.get_json(silent=True) or {}
    for field in ("name", "party", "bestiary", "day_plan", "custom_spells", "starting_hp", "starting_resources"):
        if field in body:
            setattr(campaign, field, body[field])
    db.session.commit()
    return jsonify(campaign.to_dict())


@api_bp.delete("/campaigns/<int:campaign_id>")
def delete_campaign(campaign_id: int):
    campaign = db.session.get(Campaign, campaign_id)
    if not campaign:
        return jsonify({"error": "campaign not found"}), 404
    db.session.delete(campaign)
    db.session.commit()
    return "", 204
