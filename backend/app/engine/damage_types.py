"""Damage types and the resistance/vulnerability/immunity resolution rules.

Every attack in the engine (a character's weapon swing, a monster's claw,
a legendary action, a fireball) resolves to one or more typed damage
*components* of the shape::

    {"type": "fire", "magical": True, "amount": 12.4}

Entities (characters and monsters) carry three lists that describe how they
react to incoming damage of a given type:

    resistances    -> half damage
    vulnerabilities -> double damage
    immunities     -> no damage

Each entry is ``{"type": <damage type>, "magical_only": bool}``. When
``magical_only`` is set, the resistance/vulnerability/immunity only applies
to *nonmagical* instances of that damage type - the classic "resistant to
nonmagical bludgeoning/piercing/slashing" pattern.
"""
from __future__ import annotations

from typing import Iterable, Mapping, TypedDict

DAMAGE_TYPES: list[str] = [
    "bludgeoning", "piercing", "slashing",
    "acid", "cold", "fire", "force", "lightning",
    "necrotic", "poison", "psychic", "radiant", "thunder",
]

PHYSICAL_TYPES = {"bludgeoning", "piercing", "slashing"}


class DamageComponent(TypedDict):
    """A single typed slice of damage output (one attack, one rider effect, one nova spend)."""
    source: str
    type: str
    magical: bool
    amount: float


class ResistanceEntry(TypedDict):
    type: str
    magical_only: bool


def _matches(entries: Iterable[Mapping], dtype: str, magical: bool) -> bool:
    for entry in entries or []:
        if entry.get("type") != dtype:
            continue
        if entry.get("magical_only") and magical:
            # Resistance/vulnerability/immunity is nonmagical-only and this hit is magical -> bypassed.
            continue
        return True
    return False


def combined_multiplier(entity: Mapping | None, dtype: str, magical: bool) -> float:
    """Resolve the net damage multiplier an *entity* applies to one damage component.

    Follows the standard 5e stacking rule: immune beats everything; a
    simultaneous resistance + vulnerability to the same type cancels out to
    a normal (1x) multiplier.
    """
    if not entity:
        return 1.0
    if _matches(entity.get("immunities", []), dtype, magical):
        return 0.0
    is_vulnerable = _matches(entity.get("vulnerabilities", []), dtype, magical)
    is_resistant = _matches(entity.get("resistances", []), dtype, magical)
    if is_vulnerable and is_resistant:
        return 1.0
    if is_vulnerable:
        return 2.0
    if is_resistant:
        return 0.5
    return 1.0


def apply_multiplier_to_components(
    components: Iterable[DamageComponent], entity: Mapping | None
) -> float:
    """Sum a list of damage components after applying one entity's resistance profile."""
    return sum(c["amount"] * combined_multiplier(entity, c["type"], c["magical"]) for c in components)
