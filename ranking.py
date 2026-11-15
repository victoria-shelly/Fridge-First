from __future__ import annotations

from datetime import date, datetime
import heapq
from typing import Any, Iterable

URGENCY_POINTS = {
    "red": 10,     # Expires today (0 days left)
    "yellow": 5,   # Expires soon (1–3 days left)
    "green": 1,    # Fresh (4+ days left)
    "gray": 0,     # Already expired (< 0 days left; excluded from recipes)
}


def parse_date(value: str | date | datetime) -> date:  
    """Convert a YYYY-MM-DD string, date, or datetime into a datetime.date."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value.strip())
    raise TypeError(f"Unsupported date value: {value!r}")


def compute_days_left(expires: str | date | datetime, today: str | date | datetime) -> int:
    """Return integer days remaining from today until expires."""
    return (parse_date(expires) - parse_date(today)).days


def get_urgency_color(days_left: int) -> str:
    """
    Map days_left to urgency color per FridgeFirst rules:
      - < 0 days: 'gray' (expired)
      - 0 days:   'red'
      - 1–3 days: 'yellow'
      - 4+ days:  'green'
    """
    if days_left < 0:
        return "gray"
    if days_left == 0:
        return "red"
    if days_left <= 3:
        return "yellow"
    return "green"


def get_urgency_points(days_left: int) -> int:
    """
    Map days_left to urgency score points:
      - red (0 days):      10 points
      - yellow (1–3 days): 5 points
      - green (4+ days):   1 point
      - gray (< 0 days):   0 points (not used)
    """
    return URGENCY_POINTS[get_urgency_color(days_left)]


def _extract_item_fields(item: Any, today: str | date | datetime | None = None) -> tuple[str, int]:
    """
    Extract normalized (ingredient_name, days_left) from either a FoodItem object
    (supporting item.days_left(today)) or a dictionary.
    """
    if isinstance(item, dict):
        raw_name = item.get("name", "")
        if "days_left" in item and item["days_left"] is not None:
            days = int(item["days_left"])
        elif "expires" in item and today is not None:
            days = compute_days_left(item["expires"], today)
        else:
            raise ValueError("Dict fridge item must provide 'days_left' or ('expires' and 'today').")
    else:
        raw_name = getattr(item, "name", "")
        if hasattr(item, "days_left") and callable(item.days_left):
            days = int(item.days_left(today))
        elif hasattr(item, "days_left"):
            days = int(item.days_left)
        elif hasattr(item, "expires") and today is not None:
            days = compute_days_left(item.expires, today)
        else:
            raise ValueError("FoodItem object must provide days_left(today) or expires.")

    return str(raw_name).strip().lower(), days


def _extract_recipe_fields(recipe: Any) -> tuple[str, set[str], Any]:
    """
    Extract (recipe_name, normalized_ingredient_set, recipe_id) from a Recipe object or dict.
    """
    if isinstance(recipe, dict):
        name = str(recipe.get("name", "")).strip()
        raw_ingredients: Iterable[str] = recipe.get("ingredients", ())
        recipe_id = recipe.get("id", name.lower())
    else:
        name = str(getattr(recipe, "name", "")).strip()
        raw_ingredients = getattr(recipe, "ingredients", ())
        recipe_id = getattr(recipe, "id", name.lower())

    ingredients = {str(ing).strip().lower() for ing in raw_ingredients if str(ing).strip()}
    return name, ingredients, recipe_id


def build_fridge_lookup(
    fridge_items: Iterable[Any],
    today: str | date | datetime | None = None,
) -> dict[str, dict[str, Any]]:
    """
    Build a lookup of active (non-expired) fridge items keyed by normalized ingredient name.
    If duplicate batches of the same ingredient exist, keep the most urgent non-expired one
    (smallest non-negative days_left / highest urgency points).
    """
    active_fridge: dict[str, dict[str, Any]] = {}

    for item in fridge_items:
        name, days_left = _extract_item_fields(item, today)
        if not name or days_left < 0:
            # Expired items (gray) are excluded from recipe suggestions
            continue

        color = get_urgency_color(days_left)
        points = get_urgency_points(days_left)

        existing = active_fridge.get(name)
        if existing is None or days_left < existing["days_left"]:
            active_fridge[name] = {
                "name": name,
                "days_left": days_left,
                "color": color,
                "points": points,
            }

    return active_fridge


def rank_recipes(
    recipes: Iterable[Any],
    fridge_items: Iterable[Any] | dict[str, dict[str, Any]],
    today: str | date | datetime | None = None,
) -> list[dict[str, Any]]:
    """
    Score and rank recipes deterministically using set operations and a binary heap.

    Tie-breaking order (per Team Pitch & Roles):
      1. Highest score first (-score in min-heap)
      2. Fewest missing ingredients (len(missing))
      3. Alphabetical by recipe name (name.lower())
      4. Recipe ID as final deterministic tie-breaker
    """
    if isinstance(fridge_items, dict):
        active_fridge = fridge_items
    else:
        active_fridge = build_fridge_lookup(fridge_items, today)

    active_names = set(active_fridge.keys())
    heap: list[tuple[int, int, str, str, int, dict[str, Any]]] = []

    for idx, recipe in enumerate(recipes):
        name, recipe_ingredients, recipe_id = _extract_recipe_fields(recipe)

        # Set operations: matched vs. missing ingredients
        uses_set = recipe_ingredients & active_names
        missing_set = recipe_ingredients - active_names

        score = sum(active_fridge[ing]["points"] for ing in uses_set)
        uses_sorted = sorted(
            uses_set,
            key=lambda ing: (-active_fridge[ing]["points"], active_fridge[ing]["days_left"], ing),
        )
        uses_details = [active_fridge[ing] for ing in uses_sorted]
        missing_sorted = sorted(missing_set)

        result_card = {
            "name": name,
            "score": score,
            "uses": uses_sorted,
            "uses_details": uses_details,
            "missing": missing_sorted,
        }

        heap_key = (
            -score,
            len(missing_sorted),
            name.lower(),
            str(recipe_id),
            idx,
            result_card,
        )
        heapq.heappush(heap, heap_key)

    ranked: list[dict[str, Any]] = []
    while heap:
        _, _, _, _, _, card = heapq.heappop(heap)
        ranked.append(card)

    for rank_num, card in enumerate(ranked, start=1):
        card["rank"] = rank_num

    return ranked


def plan_this_week(
    recipes: Iterable[Any],
    fridge_items: Iterable[Any] | dict[str, dict[str, Any]],
    today: str | date | datetime | None = None,
) -> list[dict[str, Any]]:
    """
    Greedily select a sequence of recipes for 'This week' that uses up as much
    expiring food as possible without reusing the same fridge item twice.
    Stops when no remaining recipe achieves a score > 0.
    """
    if isinstance(fridge_items, dict):
        remaining_fridge = dict(fridge_items)
    else:
        remaining_fridge = build_fridge_lookup(fridge_items, today)

    remaining_recipes = list(recipes)
    weekly_plan: list[dict[str, Any]] = []

    while remaining_fridge and remaining_recipes:
        ranked = rank_recipes(remaining_recipes, remaining_fridge)
        if not ranked or ranked[0]["score"] <= 0:
            break

        best = ranked[0]
        weekly_plan.append(best)

        # Consume matched fridge ingredients so they cannot be double-counted
        for used_ing in best["uses"]:
            remaining_fridge.pop(used_ing, None)

        # Remove the chosen recipe from remaining candidates
        best_name_lower = best["name"].lower()
        remaining_recipes = [
            r for r in remaining_recipes
            if _extract_recipe_fields(r)[0].lower() != best_name_lower
        ]

    for step_num, card in enumerate(weekly_plan, start=1):
        card["rank"] = step_num

    return weekly_plan