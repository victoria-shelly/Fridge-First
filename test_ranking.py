"""
Unit test suite for FridgeFirst DSA Ranking & Weekly Planner (ranking.py).
Run with: python3 -m unittest test_ranking.py -v
"""

from datetime import date
import random
import unittest

from ranking import (
    build_fridge_lookup,
    compute_days_left,
    get_urgency_color,
    get_urgency_points,
    plan_this_week,
    rank_recipes,
)


class DummyFoodItem:
    """Mock of the Data-model teammate's FoodItem class."""

    def __init__(self, name: str, expires: str):
        self.name = name
        self.expires = expires

    def days_left(self, today: str | date) -> int:
        return compute_days_left(self.expires, today)


class DummyRecipe:
    """Mock of the Data-model teammate's Recipe class."""

    def __init__(self, name: str, ingredients: set[str]):
        self.name = name
        self.ingredients = set(ingredients)


class TestFridgeFirstRanking(unittest.TestCase):
    def setUp(self) -> None:
        self.today = "2026-11-14"
        self.worked_example_fridge = [
            {"name": "Chicken", "expires": "2026-11-14"},      # 0 days -> Red (10)
            {"name": "Bell pepper", "expires": "2026-11-16"},  # 2 days -> Yellow (5)
            {"name": "Yogurt", "expires": "2026-11-19"},       # 5 days -> Green (1)
            {"name": "Eggs", "expires": "2026-11-25"},         # 11 days -> Green (1)
            {"name": "Rice", "expires": "2027-03-01"},         # 107 days -> Green (1)
            {"name": "Bread", "expires": "2026-11-13"},        # -1 days -> Gray (0, ignored)
        ]
        self.worked_example_recipes = [
            {
                "name": "Chicken stir-fry",
                "ingredients": ["chicken", "bell pepper", "rice", "soy sauce"],
            },
            {
                "name": "Egg fried rice",
                "ingredients": ["eggs", "rice", "bell pepper"],
            },
            {
                "name": "Yogurt parfait",
                "ingredients": ["yogurt", "granola"],
            },
        ]

    def test_urgency_colors_and_points_boundaries(self) -> None:
        """Verify exact color and point boundaries: today=red(10), 1-3d=yellow(5), 4+d=green(1), <0d=gray(0)."""
        cases = [
            (-5, "gray", 0),
            (-1, "gray", 0),
            (0, "red", 10),
            (1, "yellow", 5),
            (2, "yellow", 5),
            (3, "yellow", 5),
            (4, "green", 1),
            (7, "green", 1),
            (11, "green", 1),
            (120, "green", 1),
        ]
        for days_left, expected_color, expected_pts in cases:
            with self.subTest(days_left=days_left):
                self.assertEqual(get_urgency_color(days_left), expected_color)
                self.assertEqual(get_urgency_points(days_left), expected_pts)

    def test_worked_example_nov_14(self) -> None:
        """Verify the exact Nov 14 worked example from Team Pitch & Roles."""
        ranked = rank_recipes(
            self.worked_example_recipes,
            self.worked_example_fridge,
            today=self.today,
        )
        self.assertEqual(
            [r["name"] for r in ranked],
            ["Chicken stir-fry", "Egg fried rice", "Yogurt parfait"],
        )
        self.assertEqual([r["score"] for r in ranked], [16, 7, 1])

        # Verify matched and missing sets
        self.assertEqual(ranked[0]["uses"], ["chicken", "bell pepper", "rice"])
        self.assertEqual(ranked[0]["missing"], ["soy sauce"])
        self.assertEqual(ranked[1]["uses"], ["bell pepper", "eggs", "rice"])
        self.assertEqual(ranked[1]["missing"], [])
        self.assertEqual(ranked[2]["uses"], ["yogurt"])
        self.assertEqual(ranked[2]["missing"], ["granola"])

    def test_date_control_shift_to_nov_17(self) -> None:
        """If the user moves the date to Nov 17, yogurt turns yellow (5 pts) and parfait moves up."""
        ranked = rank_recipes(
            self.worked_example_recipes,
            self.worked_example_fridge,
            today="2026-11-17",
        )
        # On Nov 17: Chicken (-3) and Bell pepper (-1) are expired.
        # Yogurt (Nov 19 -> 2 days left) is Yellow (5 pts).
        # Eggs (8d) and Rice (100+d) are Green (1 pt each -> Egg fried rice = 2 pts).
        self.assertEqual(ranked[0]["name"], "Yogurt parfait")
        self.assertEqual(ranked[0]["score"], 5)
        self.assertEqual(ranked[1]["name"], "Egg fried rice")
        self.assertEqual(ranked[1]["score"], 2)
        self.assertEqual(ranked[2]["name"], "Chicken stir-fry")
        self.assertEqual(ranked[2]["score"], 1)  # Only rice is left

    def test_expired_items_never_counted(self) -> None:
        """Expired items (gray) must never be matched or contribute points."""
        recipes = [{"name": "Toast", "ingredients": ["bread"]}]
        ranked = rank_recipes(recipes, self.worked_example_fridge, today=self.today)
        self.assertEqual(ranked[0]["score"], 0)
        self.assertEqual(ranked[0]["uses"], [])
        self.assertEqual(ranked[0]["missing"], ["bread"])

    def test_red_item_beats_multiple_green_items(self) -> None:
        """A recipe using 1 red item (10 pts) beats one using 5 green items (5 pts)."""
        fridge = [
            {"name": "spinach", "days_left": 0},   # Red = 10
            {"name": "eggs", "days_left": 6},      # Green = 1
            {"name": "milk", "days_left": 7},      # Green = 1
            {"name": "cheese", "days_left": 10},   # Green = 1
            {"name": "onion", "days_left": 14},    # Green = 1
            {"name": "potato", "days_left": 20},   # Green = 1
        ]
        recipes = [
            {"name": "Country Frittata", "ingredients": ["eggs", "milk", "cheese", "onion", "potato"]},
            {"name": "Sauteed Spinach", "ingredients": ["spinach", "garlic", "olive oil"]},
        ]
        ranked = rank_recipes(recipes, fridge)
        self.assertEqual(ranked[0]["name"], "Sauteed Spinach")
        self.assertEqual(ranked[0]["score"], 10)
        self.assertEqual(ranked[1]["name"], "Country Frittata")
        self.assertEqual(ranked[1]["score"], 5)

    def test_tie_breakers_missing_count_then_alphabetical(self) -> None:
        """Equal scores break ties by fewer missing ingredients, then alphabetical by recipe name."""
        fridge = [{"name": "chicken", "days_left": 0}]  # 10 pts
        recipes = [
            {"name": "Zesty Chicken", "ingredients": ["chicken", "lemon"]},              # Score 10, 1 missing
            {"name": "Apple Glazed Chicken", "ingredients": ["chicken", "apple"]},       # Score 10, 1 missing
            {"name": "Simple Roast Chicken", "ingredients": ["chicken"]},                # Score 10, 0 missing
            {"name": "Chicken Curry", "ingredients": ["chicken", "curry", "coconut"]},   # Score 10, 2 missing
        ]
        ranked = rank_recipes(recipes, fridge)
        self.assertEqual(
            [r["name"] for r in ranked],
            [
                "Simple Roast Chicken",  # 0 missing
                "Apple Glazed Chicken",  # 1 missing, 'A' before 'Z'
                "Zesty Chicken",         # 1 missing
                "Chicken Curry",         # 2 missing
            ],
        )

    def test_deterministic_order_independent_of_input_order(self) -> None:
        """Shuffling input lists must always produce the exact same ranking."""
        baseline = rank_recipes(
            self.worked_example_recipes,
            self.worked_example_fridge,
            today=self.today,
        )
        rng = random.Random(42)
        for _ in range(10):
            shuffled_fridge = list(self.worked_example_fridge)
            shuffled_recipes = list(self.worked_example_recipes)
            rng.shuffle(shuffled_fridge)
            rng.shuffle(shuffled_recipes)
            result = rank_recipes(shuffled_recipes, shuffled_fridge, today=self.today)
            self.assertEqual(result, baseline)

    def test_plan_this_week_greedy_no_ingredient_reuse(self) -> None:
        """Weekly planner greedily picks top recipes and removes used items so nothing is double-counted."""
        # After Chicken stir-fry uses chicken, bell pepper, and rice:
        # remaining active items are eggs (1 pt) and yogurt (1 pt).
        # Egg fried rice now only matches eggs (score 1, missing rice & bell pepper -> 2 missing).
        # Yogurt parfait matches yogurt (score 1, missing granola -> 1 missing), so Yogurt parfait wins #2!
        plan = plan_this_week(
            self.worked_example_recipes,
            self.worked_example_fridge,
            today=self.today,
        )
        self.assertEqual(
            [r["name"] for r in plan],
            ["Chicken stir-fry", "Yogurt parfait", "Egg fried rice"],
        )
        self.assertEqual([r["score"] for r in plan], [16, 1, 1])
        # Confirm Egg fried rice no longer claims rice or bell pepper in step 3
        self.assertEqual(plan[2]["uses"], ["eggs"])
        self.assertEqual(plan[2]["missing"], ["bell pepper", "rice"])

    def test_works_with_data_model_class_instances(self) -> None:
        """Verify seamless integration with FoodItem and Recipe class instances."""
        items = [
            DummyFoodItem("Chicken", "2026-11-14"),
            DummyFoodItem("Bell pepper", "2026-11-16"),
            DummyFoodItem("Bread", "2026-11-13"),
        ]
        recipes = [
            DummyRecipe("Pepper Chicken", {"chicken", "bell pepper", "garlic"}),
            DummyRecipe("Bread Pudding", {"bread", "milk"}),
        ]
        lookup = build_fridge_lookup(items, today=self.today)
        self.assertIn("chicken", lookup)
        self.assertNotIn("bread", lookup)

        ranked = rank_recipes(recipes, items, today=self.today)
        self.assertEqual(ranked[0]["name"], "Pepper Chicken")
        self.assertEqual(ranked[0]["score"], 15)
        self.assertEqual(ranked[1]["name"], "Bread Pudding")
        self.assertEqual(ranked[1]["score"], 0)


if __name__ == "__main__":
    unittest.main()