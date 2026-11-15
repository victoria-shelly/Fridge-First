"""Shopping list helpers — merge missing ingredients with no duplicates."""

from __future__ import annotations

from models import normalize_name


def normalize(name):
    return normalize_name(name)


def build_shopping_list(chosen_recipes, fridge_names):
    fridge_set = {normalize(name) for name in fridge_names}
    by_item = {}

    for recipe in chosen_recipes:
        if hasattr(recipe, "ingredients"):
            ingredients = recipe.ingredients
            recipe_name = recipe.name
        else:
            ingredients = recipe.get("ingredients", [])
            recipe_name = recipe.get("name", "")

        recipe_set = {normalize(ingredient) for ingredient in ingredients}
        missing_items = recipe_set - fridge_set
        for item in missing_items:
            by_item.setdefault(item, [])
            if recipe_name not in by_item[item]:
                by_item[item].append(recipe_name)

    return [
        {"item": item, "for_recipes": sorted(by_item[item])}
        for item in sorted(by_item)
    ]


def missing_names(chosen_recipes, fridge_names):
    return [row["item"] for row in build_shopping_list(chosen_recipes, fridge_names)]
