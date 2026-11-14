"""DSA / data-model smoke tests for the pitch worked example."""

from datetime import date

from models import FoodItem, Recipe
from ranking import match_recipe, rank_recipes
from security import plain_text, validate_date, validate_name


def sample_fridge():
    return [
        FoodItem("chicken", "2026-11-14"),
        FoodItem("bell pepper", "2026-11-16"),
        FoodItem("yogurt", "2026-11-19"),
        FoodItem("eggs", "2026-11-25"),
        FoodItem("rice", "2027-03-01"),
        FoodItem("bread", "2026-11-13"),
    ]


def sample_recipes():
    return [
        Recipe("Chicken stir-fry", {"chicken", "bell pepper", "rice", "soy sauce"}),
        Recipe("Egg fried rice", {"eggs", "rice", "bell pepper"}),
        Recipe("Yogurt parfait", {"yogurt", "granola"}),
    ]


def test_colors_for_nov_14():
    today = date(2026, 11, 14)
    fridge = {item.name: item for item in sample_fridge()}
    assert fridge["chicken"].status(today) == "red"
    assert fridge["bell pepper"].status(today) == "yellow"
    assert fridge["yogurt"].status(today) == "green"
    assert fridge["bread"].status(today) == "gray"


def test_stir_fry_scores_16_and_ranks_first():
    today = "2026-11-14"
    ranked = rank_recipes(sample_recipes(), sample_fridge(), today)
    assert ranked[0]["name"] == "Chicken stir-fry"
    assert ranked[0]["score"] == 16
    assert ranked[0]["missing"] == ["soy sauce"]
    assert ranked[1]["name"] == "Egg fried rice"
    assert ranked[1]["score"] == 7


def test_expired_items_do_not_score():
    today = "2026-11-14"
    recipe = Recipe("Toast", {"bread"})
    matched = match_recipe(recipe, sample_fridge(), today)
    assert matched["score"] == 0
    assert matched["uses"] == []


def test_security_escapes_and_rejects_bad_input():
    assert "&lt;script&gt;" in plain_text("<script>")
    try:
        validate_name("x" * 10_000)
        assert False, "expected long name to fail"
    except ValueError:
        pass
    try:
        validate_date("9999-99-99")
        assert False, "expected bad date to fail"
    except ValueError:
        pass


if __name__ == "__main__":
    test_colors_for_nov_14()
    test_stir_fry_scores_16_and_ranks_first()
    test_expired_items_do_not_score()
    test_security_escapes_and_rejects_bad_input()
    print("all tests passed")
