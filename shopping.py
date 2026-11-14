"""Python role: shopping list — merge missing ingredients, no duplicates."""

from __future__ import annotations

import db
from models import normalize_name


def merge_missing(ingredient_lists: list[list[str]]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for group in ingredient_lists:
        for raw in group:
            name = normalize_name(raw)
            if not name or name in seen:
                continue
            seen.add(name)
            merged.append(name)
    return merged


def add_from_missing(missing: list[str]) -> list[str]:
    return db.add_shopping_items(missing)


def get_list() -> list[str]:
    return db.list_shopping()
