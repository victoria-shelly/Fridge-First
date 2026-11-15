from models import FoodItem, Recipe
import pytest
from datetime import date
def test_food_item_status():
    today = date(2024, 6, 1)
    item1 = FoodItem("Milk", "2024-05-30", 2.5)  # Expired
    item2 = FoodItem("Eggs", "2024-06-01", 3.0)  # Expires today
    item3 = FoodItem("Cheese", "2024-06-03", 5.0)  # Expires in 2 days
    item4 = FoodItem("Butter", "2024-06-10", 4.0)  # Expires in 9 days

    assert item1.status(today) == "expired"
    assert item2.status(today) == "red"
    assert item3.status(today) == "yellow"
    assert item4.status(today) == "green"
def test_food_item_to_dict():
    today = date(2024, 6, 1)
    item = FoodItem("Yogurt", "2024-06-05", 1.5)
    expected_dict = {
        "name": "yogurt",
        "expires": "2024-06-05",
        "price": 1.5,
        "days_left": 4,
        "status": "yellow"
    }
    assert item.to_dict(today) == expected_dict
def test_food_item_days_left():
    today = date(2024, 6, 1)
    item = FoodItem("Juice", "2024-06-04", 2.0)
    assert item.days_left(today) == 3
def test_recipe_can_make():
    recipe = Recipe("Pancakes", ["flour", "milk", "eggs"], ["Mix ingredients", "Cook on skillet"])
    pantry_items = {"flour", "milk", "eggs", "sugar"}
    assert recipe.can_make(pantry_items) == True

    pantry_items_missing = {"flour", "milk"}
    assert recipe.can_make(pantry_items_missing) == False
def test_recipe_to_dict_and_from_dict():
    recipe = Recipe("Salad", ["lettuce", "tomato", "cucumber"], ["Chop vegetables", "Mix together"])
    recipe_dict = recipe.to_dict()
    
    # Check if to_dict returns the expected structure
    assert recipe_dict == {
        "name": "Salad",
        "ingredients": ["cucumber", "lettuce", "tomato"],  # Sorted order
        "steps": ["Chop vegetables", "Mix together"]
    }
    
    # Now test from_dict
    new_recipe = Recipe.from_dict(recipe_dict)
    assert new_recipe.name == recipe.name
    assert new_recipe.ingredients == recipe.ingredients
    assert new_recipe.steps == recipe.steps