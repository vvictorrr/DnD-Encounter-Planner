from datetime import datetime, timezone

from .extensions import db


class Campaign(db.Model):
    """A saved campaign: a party, a bestiary, a day plan, a spell library,
    and the party's starting conditions for that day.

    The nested game data (a character's feats, a monster's attack list, ...)
    is naturally document-shaped and gets edited as a whole object from the
    frontend, so it's stored as JSON columns rather than normalized across a
    dozen tables. The columns it *is* worth being able to query on directly
    (name, timestamps) stay as real columns.
    """
    __tablename__ = "campaigns"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, default="Untitled Campaign")

    party = db.Column(db.JSON, nullable=False, default=list)
    bestiary = db.Column(db.JSON, nullable=False, default=list)
    day_plan = db.Column(db.JSON, nullable=False, default=list)
    custom_spells = db.Column(db.JSON, nullable=False, default=list)
    starting_hp = db.Column(db.JSON, nullable=False, default=dict)
    starting_resources = db.Column(db.JSON, nullable=False, default=dict)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "party": self.party,
            "bestiary": self.bestiary,
            "day_plan": self.day_plan,
            "custom_spells": self.custom_spells,
            "starting_hp": self.starting_hp,
            "starting_resources": self.starting_resources,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
