"""Encounter-difficulty math, 2014 DMG rules only.

The planner deliberately doesn't support the 2024 DMG's difficulty tables.
The community DPR data this project calibrates against (the Optimists'
Guide to D&D 5E Damage by Class) is 2014-rules math, and the two editions'
class features/subclasses diverge enough that supporting both faithfully
would mean either a second full subclass/spell dataset or a misleading
"one size fits both" approximation. Better to be exactly right about one
edition than vaguely right about two.
"""
from __future__ import annotations

# Per-character XP thresholds, DMG (2014) p.82.
XP_THRESHOLDS = {
    1: {"easy": 25, "medium": 50, "hard": 75, "deadly": 100},
    2: {"easy": 50, "medium": 100, "hard": 150, "deadly": 200},
    3: {"easy": 75, "medium": 150, "hard": 225, "deadly": 400},
    4: {"easy": 125, "medium": 250, "hard": 375, "deadly": 500},
    5: {"easy": 250, "medium": 500, "hard": 750, "deadly": 1100},
    6: {"easy": 300, "medium": 600, "hard": 900, "deadly": 1400},
    7: {"easy": 350, "medium": 750, "hard": 1100, "deadly": 1700},
    8: {"easy": 450, "medium": 900, "hard": 1400, "deadly": 2100},
    9: {"easy": 550, "medium": 1100, "hard": 1600, "deadly": 2400},
    10: {"easy": 600, "medium": 1200, "hard": 1900, "deadly": 2800},
    11: {"easy": 800, "medium": 1600, "hard": 2400, "deadly": 3600},
    12: {"easy": 1000, "medium": 2000, "hard": 3000, "deadly": 4500},
    13: {"easy": 1100, "medium": 2200, "hard": 3400, "deadly": 5100},
    14: {"easy": 1250, "medium": 2500, "hard": 3800, "deadly": 5700},
    15: {"easy": 1400, "medium": 2800, "hard": 4300, "deadly": 6400},
    16: {"easy": 1600, "medium": 3200, "hard": 4800, "deadly": 7200},
    17: {"easy": 2000, "medium": 3900, "hard": 5900, "deadly": 8800},
    18: {"easy": 2100, "medium": 4200, "hard": 6300, "deadly": 9500},
    19: {"easy": 2400, "medium": 4900, "hard": 7300, "deadly": 10900},
    20: {"easy": 2800, "medium": 5700, "hard": 8500, "deadly": 12700},
}


def multiplier(monster_count: int) -> float:
    """The monster-count XP multiplier (DMG p.82): more monsters means more
    actions per round than their raw XP total implies."""
    if monster_count <= 1:
        return 1.0
    if monster_count == 2:
        return 1.5
    if monster_count <= 6:
        return 2.0
    if monster_count <= 10:
        return 2.5
    if monster_count <= 14:
        return 3.0
    return 4.0


def party_adjusted_multiplier(monster_count: int, party_size: int) -> float:
    """Shift the multiplier one column if the party isn't the assumed 3-5 members."""
    cols = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0]
    idx = cols.index(multiplier(monster_count))
    if party_size <= 2:
        idx = min(len(cols) - 1, idx + 1)
    if party_size >= 6:
        idx = max(0, idx - 1)
    return cols[idx]


def difficulty_label(total_xp: float, avg_party_level: int, party_size: int) -> dict:
    """Return ``{"text": str, "tone": str, "budget": float}`` for a given
    (already monster-count-adjusted) total encounter XP."""
    level = min(20, max(1, avg_party_level))
    th = XP_THRESHOLDS[level]
    total = {k: v * party_size for k, v in th.items()}
    if total_xp >= total["deadly"]:
        return {"text": "Deadly", "tone": "danger", "budget": total["deadly"]}
    if total_xp >= total["hard"]:
        return {"text": "Hard", "tone": "warn", "budget": total["deadly"]}
    if total_xp >= total["medium"]:
        return {"text": "Medium", "tone": "good", "budget": total["deadly"]}
    if total_xp >= total["easy"]:
        return {"text": "Easy", "tone": "good", "budget": total["deadly"]}
    return {"text": "Trivial", "tone": "good", "budget": total["deadly"]}
