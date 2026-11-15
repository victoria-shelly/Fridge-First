# Built-in (no install needed)
from datetime import date
import json

# Installed libraries
from flask import Flask, request, jsonify, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Your files
from stats import build_stats
from shopping import build_shopping_list

# Teammates' files
from ranking import rank_recipes, plan_week
from db import (init_db, add_item, listActiveItems, mark_used,
                throw_out, add_recipe, listRecipes, get_log)
from models import FoodItem, Recipe
from security import validate_item, validate_recipe



app = Flask(__name__)

limiter = setup_security(app)

init_db()


def eatToday():
    input_key=request.args.get("today")
    
    
    try:
        return date.fromisoformat(input_key)
    except(ValueError, TypeError):
        return None
    
    if input_key is None:
        return None
    
def error(messages, status=400):
    return {"errors": messages}, status




@app.route("/")
def index():
    return render_template("index.html")


@app.route("/items", methods = ["GET"])

def get_items():
    
    today = eatToday()
    if today is None:
        return error(["Please enter a valid date"])
    
    
    items = listActiveItems()
    
    for item in items:
        item.to_dict(today)
        
    items = sorted(items, key=lambda item: item["days left"])
    
    return jsonify(items)

@app.route("/items", methods = ["POST"])

#@limiter.limit("20 per minute")

def create_item():
    
    dict = request.get_json(silent=True)
    
    if dict is None:
        return error(["Send as JSON"])
        
    issues = validate_item(dict)
    if issues:
        return error(issues)
    
    name = dict["name"]
    expiryDate = dict.fromisoformat(dict["expires"])
    cost = dict.get("cost",0)
    savedItem = add_item(name, expiryDate, cost)
    return savedItem, 201

@app.route("/items/<int:item_id>/throw-out/",methods=["POST"])
def throwOutItem(ID):
    today = eatToday()
    if today is None:
        return error(["Plese enter valid date as of today=YYYY-MM-DD"])
    worked = throw_out(ID, today);
    if not worked:
        return error(["No item with that ID"], 404)
    return {"thrown_out": ID}


@app.route("/recipes", methods=["GET"])
def getRecipes():
    """List all recipes (built-in file plus custom ones)."""
    return jsonify(listRecipes())


@app.route("/recipes", methods=["POST"])
def create_recipe():
    data = request.get_json(silent=True)
    if data is None:
        return error(["Please send the recipe as JSON"])

    problems = validate_recipe(data)
    if problems:
        return error(problems)

    saved = add_recipe(data["name"], data["ingredients"], data.get("steps", []))

    return saved, 201



@app.route("/rank", methods=["GET"])
def getRanking():
    """Ranked recipe suggestions for today."""
    today = eatToday()
    if today is None:
        return error(["Please enter a valid date as today=YYYY-MM-DD"])

    ranked = rank_recipes(listActiveItems(), listRecipes(), today)

    return jsonify(ranked)


@app.route("/plan", methods=["GET"])
def getPlan():
    """Weekly plan: a set of recipes that uses the most expiring food."""
    # Get the date, or stop with a 400.
    today = eatToday()
    if today is None:
        return error(["Please enter a valid date as today=YYYY-MM-DD"])

    # Optional ?count=N; type=int converts it, and a bad value falls back to 5.
    count = request.args.get("count", default=5, type=int)

    # Hand everything to the DSA lead's greedy planner.
    plan = plan_week(listActiveItems(), listRecipes(), today, count)

    # Send the plan back as JSON.
    return jsonify(plan)


# ---------------------------------------------------------------------------
# Cook a recipe
# ---------------------------------------------------------------------------

# Connect POST /cook to the function below.
@app.route("/cook", methods=["POST"])
@limiter.limit("20 per minute")
def cook():
    """Mark a recipe as cooked: its fridge ingredients are used and logged as saved."""
    # Get the date, or stop with a 400.
    today = eatToday()
    if today is None:
        return error(["Please enter a valid date as today=YYYY-MM-DD"])

    # Read the JSON body: {"name": "Chicken stir-fry"}.
    data = request.get_json(silent=True)
    if data is None or "name" not in data:
        return error(["Please send the recipe name as JSON"])

    # Look the recipe up by name; 404 if it doesn't exist.
    recipe = find_recipe(data["name"])
    if recipe is None:
        return error(["No recipe with that name"], 404)

    # Ingredients that are both in the recipe AND fresh in the fridge (set intersection).
    used = set(recipe["ingredients"]) & fresh_fridge_names(today)

    # Mark them used; db.py also logs each one as saved.
    mark_used(sorted(used), today)

    # Report what was used, sorted so the order is always the same.
    return {"used": sorted(used), "saved_count": len(used)}


# ---------------------------------------------------------------------------
# Shopping list and stats (these call YOUR files)
# ---------------------------------------------------------------------------

# Connect POST /shopping-list to the function below.
@app.route("/shopping-list", methods=["POST"])
def shopping_list():
    """Items to buy for the chosen recipes."""
    # Get the date (expired items count as missing), or stop with a 400.
    today = eatToday()
    if today is None:
        return error(["Please enter a valid date as today=YYYY-MM-DD"])

    # Read the JSON body: {"recipes": ["Chicken stir-fry", ...]}.
    data = request.get_json(silent=True)
    if data is None or not isinstance(data.get("recipes"), list):
        return error(["Please send a list of recipe names as JSON"])

    # Turn each name into its recipe dict, then drop names that don't exist.
    chosen = [find_recipe(name) for name in data["recipes"]]
    chosen = [recipe for recipe in chosen if recipe is not None]

    # Call YOUR shopping.py function with the chosen recipes and the fresh fridge.
    result = build_shopping_list(chosen, fresh_fridge_names(today))

    # Send the list back as JSON.
    return jsonify(result)


# Connect GET /stats to the function below.
@app.route("/stats", methods=["GET"])
def stats():
    """Saved vs. wasted totals, money saved, and a 7-day breakdown."""
    # Get the date (the 7-day window ends here), or stop with a 400.
    today = eatToday()
    if today is None:
        return error(["Please enter a valid date as today=YYYY-MM-DD"])

    # Get the log from db.py and pass it to YOUR stats.py function.
    return build_stats(get_log(), today)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

# Start the server only when this file is run directly (not when tests import it).
if __name__ == "__main__":
    app.run(debug=True)

    
    

