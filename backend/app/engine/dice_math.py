"""Core probability math: hit/save chance and expected dice damage.

Kept deliberately tiny and dependency-free so it's trivial to unit test and
trivial to read - this is the mathematical foundation everything else in the
engine is built on.
"""
from __future__ import annotations


def hit_chance(bonus: float, target: float) -> float:
    """Chance an attack roll (or a saving throw) meets or beats ``target``.

    A natural 1 always misses and a natural 20 always hits, regardless of
    modifiers, which is why the "roll needed" is clamped to [2, 20].
    """
    needed = max(2, min(20, target - bonus))
    return (21 - needed) / 20


def die_avg(count: float, sides: float) -> float:
    """Average result of rolling ``count`` dice of ``sides`` faces."""
    return count * (sides + 1) / 2


def crit_split(hit_pct: float, crit_chance: float = 1 / 20) -> tuple[float, float]:
    """Split a hit chance into (normal-hit chance, crit chance).

    A natural 20 always both hits and crits, so crit chance is a fixed 1/20
    carved out of whatever the overall hit chance already is.
    """
    crit = crit_chance
    normal = max(0.0, hit_pct - crit)
    return normal, crit


def expected_attack_damage(bonus: float, target_ac: float, dice_avg: float, flat: float) -> float:
    """Expected damage of a single attack (one swing), accounting for crits doubling dice."""
    hp = hit_chance(bonus, target_ac)
    normal, crit = crit_split(hp)
    per_hit = dice_avg + flat
    per_crit = 2 * dice_avg + flat
    return normal * per_hit + crit * per_crit
