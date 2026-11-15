from datetime import date
import json

from flask import Flask, request, jsonify, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from stats import build_stats
from shopping import build_shopping_list

from ranking import rank_recipes, plan_week
from db import (init_db, add_item, list_active_items, mark_used,
                throw_out, add_recipe, list_recipes, get_log)
from models import FoodItem, Recipe
from security import validate_item, validate_recipe



app = Flask(__name__)

limiter = Limiter(get_remote_address, app=app)


init_db()


def get_today():
    input_key=request.args.get("today")
    
    
    try:
        return date.fromisoformat(input_key)
    except(ValueError, TypeError):
        return None
    
    if input_key is None:
        return None
    
def error(messages, status=400):
    return {"errors": messages}, status


def fresh_fridge_names(today):
    items = list_active_items()
    return {item.name for item in items if item.status(today) != "expired"}


def find_recipe(name):
    for recipe in list_recipes():
        if recipe["name"].strip().lower() == name.strip().lower():
            return recipe
    return None




@app.route("/")
def index():
    return render_template("index.html")


@app.route("/items", methods = ["GET"])

def get_items():
    
    today = get_today()
    if today is None:
        return error(["Please enter a valid date"])
    
    
    items = list_active_items()
    
    for item in items:
        item.to_dict(today)
        
    items = sorted(items, key=lambda item: item["days left"])
    
    return jsonify(items)

@app.route("/items", methods = ["POST"])

@limiter.limit("20 per minute")

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
def throw_out_item(ID):
    today = get_today()
    if today is None:
        return error(["Plese enter valid date as of today=YYYY-MM-DD"])
    worked = throw_out(ID, today);
    if not worked:
        return error(["No item with that ID"], 404)
    return {"thrown_out": ID}


@app.route("/recipes", methods=["GET"])
def get_recipes():
    return jsonify(list_recipes())


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
def get_ranking():

    today = get_today()
    if today is None:
        return error(["Please enter a valid date as today=YYYY-MM-DD"])

    ranked = rank_recipes(list_active_items(), list_recipes(), today)

    return jsonify(ranked)


@app.route("/plan", methods=["GET"])
def get_plan():

    today = get_today()
    if today is None:
        return error(["Please enter a valid date as today=YYYY-MM-DD"])

    count = request.args.get("count", default=5, type=int)

    plan = plan_week(list_active_items(), list_recipes(), today, count)

    return jsonify(plan)


@app.route("/cook", methods=["POST"])
@limiter.limit("20 per minute")
def cook():

    today = get_today()
    if today is None:
        return error(["Please enter a valid date as today=YYYY-MM-DD"])


    data = request.get_json(silent=True)
    if data is None or "name" not in data:
        return error(["Please send the recipe name as JSON"])


    recipe = find_recipe(data["name"])
    if recipe is None:
        return error(["No recipe with that name"], 404)

    used = set(recipe["ingredients"]) & fresh_fridge_names(today)

    mark_used(sorted(used), today)

    return {"used": sorted(used), "saved_count": len(used)}



@app.route("/shopping-list", methods=["POST"])
def shopping_list():
    today = get_today()
    if today is None:
        return error(["Please enter a valid date as today=YYYY-MM-DD"])

    data = request.get_json(silent=True)
    if data is None or not isinstance(data.get("recipes"), list):
        return error(["Please send a list of recipe names as JSON"])

    chosen = [find_recipe(name) for name in data["recipes"]]
    chosen = [recipe for recipe in chosen if recipe is not None]

    result = build_shopping_list(chosen, fresh_fridge_names(today))

    return jsonify(result)


@app.route("/stats", methods=["GET"])
def stats():

    today = get_today()
    if today is None:
        return error(["Please enter a valid date as today=YYYY-MM-DD"])

    return build_stats(get_log(), today)



if __name__ == "__main__":
    app.run(debug=True)