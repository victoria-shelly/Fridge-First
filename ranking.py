"""DSA role: urgency, set matching, scoring, heap ranking, This-week plan."""

from __future__ import annotations

import heapq
from datetime import date

from models import FoodItem, Recipe, normalize_name, parse_date


def urgency_points_for_days(days_left: int) -> int:
    if days_left < 0:
        return 0
    if days_left == 0:
        return 10
    if days_left <= 3:
        return 5
    return 1


def match_recipe(
    recipe: Recipe,
    fridge: list[FoodItem],
    today: date | str,
) -> dict:
    today_d = parse_date(today)
    # Prefer the most urgent copy when duplicates exist.
    by_name: dict[str, FoodItem] = {}
    for item in fridge:
        current = by_name.get(item.name)
        if current is None or item.days_left(today_d) < current.days_left(today_d):
            by_name[item.name] = item

    uses = []
    score = 0
    for name in sorted(recipe.ingredients):
        item = by_name.get(name)
        if item is None:
            continue
        points = item.urgency_points(today_d)
        if points <= 0:
            continue
        uses.append(
            {
                "name": item.name,
                "color": item.status(today_d),
                "urgency_points": points,
            }
        )
        score += points

    missing = sorted(recipe.ingredients - set(by_name.keys()))
    return {
        "name": recipe.name,
        "uses": uses,
        "missing": missing,
        "score": score,
        "custom": recipe.custom,
    }


def rank_recipes(
    recipes: list[Recipe],
    fridge: list[FoodItem],
    today: date | str,
) -> list[dict]:
    """Highest score first; fewer missing; then alphabetical name."""
    heap: list[tuple] = []
    for index, recipe in enumerate(recipes):
        ranked = match_recipe(recipe, fridge, today)
        # Negate score for max-heap behavior via heapq (min-heap).
        heapq.heappush(
            heap,
            (
                -ranked["score"],
                len(ranked["missing"]),
                ranked["name"].lower(),
                index,
                ranked,
            ),
        )

    ordered = []
    while heap:
        ordered.append(heapq.heappop(heap)[-1])
    return ordered


def this_week_plan(
    recipes: list[Recipe],
    fridge: list[FoodItem],
    today: date | str,
    limit: int = 3,
) -> list[dict]:
    """
    Greedy: repeatedly pick the highest-ranked recipe that still uses at least
    one remaining fridge item, without reusing the same single item twice.
    """
    remaining = list(fridge)
    plan: list[dict] = []
    used_names: set[str] = set()

    for _ in range(limit):
        ranked = rank_recipes(recipes, remaining, today)
        pick = None
        for candidate in ranked:
            uses = [u["name"] for u in candidate["uses"]]
            if not uses:
                continue
            if any(name in used_names for name in uses):
                continue
            pick = candidate
            break
        if pick is None:
            break
        plan.append(pick)
        for use in pick["uses"]:
            used_names.add(normalize_name(use["name"]))
        remaining = [item for item in remaining if item.name not in used_names]

    return plan
