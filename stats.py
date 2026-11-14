"""Python role: impact stats (saved vs wasted, rough money saved)."""

from __future__ import annotations

import db

# Rough average grocery cost per item for demo estimates.
AVG_ITEM_COST_USD = 3.5


def get_stats() -> dict:
    counts = db.impact_counts()
    saved = counts.get("saved", 0)
    wasted = counts.get("wasted", 0)
    return {
        "saved_count": saved,
        "wasted_count": wasted,
        "estimated_money_saved": round(saved * AVG_ITEM_COST_USD, 2),
    }


def record_saved(names: list[str], today: str) -> None:
    for name in names:
        db.log_impact("saved", name, today)


def record_wasted(name: str, today: str) -> None:
    db.log_impact("wasted", name, today)
