from datetime import date

from models import FoodItem, Recipe


def test_food_item_status():
    today = date(2024, 6, 1)
    item1 = FoodItem("Milk", "2024-05-30", 2.5)
    item2 = FoodItem("Eggs", "2024-06-01", 3.0)
    item3 = FoodItem("Cheese", "2024-06-03", 5.0)
    item4 = FoodItem("Butter", "2024-06-10", 4.0)

    assert item1.status(today) == "gray"
    assert item2.status(today) == "red"
    assert item3.status(today) == "yellow"
    assert item4.status(today) == "green"


def test_food_item_to_dict():
    today = date(2024, 6, 1)
    item = FoodItem("Yogurt", "2024-06-05", 1.5)
    payload = item.to_dict(today)
    assert payload["name"] == "yogurt"
    assert payload["expires"] == "2024-06-05"
    assert payload["expires_on"] == "2024-06-05"
    assert payload["price"] == 1.5
    assert payload["days_left"] == 4
    assert payload["status"] == "green"
    assert payload["color"] == "green"


def test_food_item_days_left():
    today = date(2024, 6, 1)
    item = FoodItem("Juice", "2024-06-04", 2.0)
    assert item.days_left(today) == 3


def test_recipe_can_make():
    recipe = Recipe("Pancakes", ["flour", "milk", "eggs"], ["Mix ingredients", "Cook on skillet"])
    assert recipe.can_make({"flour", "milk", "eggs", "sugar"}) is True
    assert recipe.can_make({"flour", "milk"}) is False


def test_recipe_to_dict_and_from_dict():
    recipe = Recipe("Salad", ["lettuce", "tomato", "cucumber"], ["Chop vegetables", "Mix together"])
    recipe_dict = recipe.to_dict()
    assert recipe_dict["name"] == "Salad"
    assert recipe_dict["ingredients"] == ["cucumber", "lettuce", "tomato"]
    assert recipe_dict["steps"] == ["Chop vegetables", "Mix together"]

    new_recipe = Recipe.from_dict(recipe_dict)
    assert new_recipe.name == recipe.name
    assert new_recipe.ingredients == recipe.ingredients
    assert new_recipe.steps == recipe.steps
