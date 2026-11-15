"""Flask API + page wiring for Fridge-First."""

from __future__ import annotations

from datetime import date

from flask import Flask, jsonify, render_template, request

import db
import security
import shopping
import stats
from ranking import plan_week_for_api, rank_recipes_for_api

app = Flask(__name__)
db.init_db()


@app.after_request
def apply_security_headers(response):
    for key, value in security.security_headers().items():
        response.headers[key] = value
    return response


def error(messages, status=400):
    if isinstance(messages, str):
        messages = [messages]
    return jsonify({"errors": messages, "error": messages[0] if messages else "error"}), status


def parse_today():
    raw = request.args.get("today")
    if request.is_json:
        payload = request.get_json(silent=True) or {}
        raw = payload.get("today", raw)
    try:
        return date.fromisoformat(security.validate_today(raw))
    except ValueError as exc:
        raise ValueError(str(exc)) from exc


def find_recipe(name: str):
    needle = name.strip().lower()
    for recipe in db.list_recipes():
        if recipe.name.strip().lower() == needle:
            return recipe
    return None


def fresh_fridge_names(today):
    return {item.name for item in db.list_active_items() if item.status(today) != "gray"}


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/ingredients")
def api_ingredients():
    return jsonify(db.load_ingredients())


@app.get("/api/items")
@app.get("/items")
def get_items():
    try:
        today = parse_today()
    except ValueError as exc:
        return error(str(exc))

    items = [item.to_dict(today) for item in db.list_active_items()]
    order = {"red": 0, "yellow": 1, "green": 2, "gray": 3}
    items.sort(key=lambda row: (order[row["color"]], row["days_left"], row["name"]))
    return jsonify({"today": today.isoformat(), "items": items})


@app.post("/api/items")
@app.post("/items")
def create_item():
    data = request.get_json(silent=True)
    if data is None:
        return error("Send as JSON")

    issues = security.validate_item(data)
    if issues:
        return error(issues)

    try:
        today = parse_today()
        name = security.validate_name(data.get("name"))
        expires = security.validate_date(data.get("expires_on", data.get("expires")))
        price = float(data.get("cost", data.get("price", 0)) or 0)
    except ValueError as exc:
        return error(str(exc))

    saved = db.add_item(name, expires, price)
    return jsonify(saved.to_dict(today)), 201


@app.post("/api/items/<int:item_id>/throw")
@app.post("/api/items/<int:item_id>/throw-out")
@app.post("/items/<int:item_id>/throw-out")
@app.post("/items/<int:item_id>/throw-out/")
def throw_out_item(item_id: int):
    try:
        today = parse_today()
    except ValueError as exc:
        return error(str(exc))

    worked = db.throw_out(item_id, today)
    if not worked:
        return error("No item with that ID", 404)
    return jsonify({"thrown_out": item_id, "stats": stats.build_stats(db.get_log(), today)})


@app.post("/api/sample-fridge")
@app.post("/sample-fridge")
def sample_fridge():
    try:
        today = parse_today()
    except ValueError as exc:
        return error(str(exc))
    items = [item.to_dict(today) for item in db.load_sample_fridge()]
    return jsonify({"today": today.isoformat(), "items": items})


@app.get("/api/recipes")
@app.get("/recipes")
def get_recipes():
    return jsonify([recipe.to_dict() for recipe in db.list_recipes()])


@app.post("/api/recipes")
@app.post("/recipes")
def create_recipe():
    data = request.get_json(silent=True)
    if data is None:
        return error("Please send the recipe as JSON")

    issues = security.validate_recipe(data)
    if issues:
        return error(issues)

    try:
        name = security.validate_name(data.get("name"), field="recipe name")
        ingredients = security.validate_ingredients(data.get("ingredients"))
    except ValueError as exc:
        return error(str(exc))

    saved = db.add_recipe(name, ingredients, data.get("steps", []))
    return jsonify(saved.to_dict()), 201


@app.get("/api/rank")
@app.get("/rank")
def get_ranking():
    try:
        today = parse_today()
    except ValueError as exc:
        return error(str(exc))

    ranked = rank_recipes_for_api(db.list_recipes(), db.list_active_items(), today=today)
    return jsonify({"today": today.isoformat(), "recipes": ranked})


@app.get("/api/this-week")
@app.get("/api/plan")
@app.get("/plan")
def get_plan():
    try:
        today = parse_today()
    except ValueError as exc:
        return error(str(exc))

    count = request.args.get("count", default=5, type=int)
    plan = plan_week_for_api(db.list_recipes(), db.list_active_items(), today=today, count=count)
    return jsonify({"today": today.isoformat(), "plan": plan})


@app.post("/api/cook")
@app.post("/cook")
def cook():
    try:
        today = parse_today()
    except ValueError as exc:
        return error(str(exc))

    data = request.get_json(silent=True) or {}
    recipe_name = data.get("recipe_name", data.get("name"))
    if not recipe_name:
        return error("Please send the recipe name as JSON")

    recipe = find_recipe(recipe_name)
    if recipe is None:
        return error("No recipe with that name", 404)

    before = fresh_fridge_names(today)
    used = sorted(set(recipe.ingredients) & before)
    removed = db.mark_used(used, today)
    missing = sorted(set(recipe.ingredients) - before)
    shopping_list = db.add_shopping_items(missing)
    return jsonify(
        {
            "recipe": recipe.name,
            "used": removed,
            "removed": removed,
            "saved_count": len(removed),
            "missing_added": missing,
            "shopping_list": shopping_list,
            "stats": stats.build_stats(db.get_log(), today),
        }
    )


@app.get("/api/shopping-list")
@app.get("/shopping-list")
def get_shopping_list():
    return jsonify({"items": db.list_shopping()})


@app.post("/api/shopping-list")
@app.post("/shopping-list")
def post_shopping_list():
    try:
        today = parse_today()
    except ValueError as exc:
        return error(str(exc))

    data = request.get_json(silent=True)
    if data is None or not isinstance(data.get("recipes"), list):
        return error("Please send a list of recipe names as JSON")

    chosen = [find_recipe(name) for name in data["recipes"]]
    chosen = [recipe for recipe in chosen if recipe is not None]
    result = shopping.build_shopping_list(chosen, fresh_fridge_names(today))
    db.add_shopping_items([row["item"] for row in result])
    return jsonify({"items": db.list_shopping(), "details": result})


@app.get("/api/stats")
@app.get("/stats")
def get_stats():
    raw = request.args.get("today")
    today = None
    if raw:
        try:
            today = date.fromisoformat(security.validate_today(raw))
        except ValueError as exc:
            return error(str(exc))
    return jsonify(stats.build_stats(db.get_log(), today))


if __name__ == "__main__":
    app.run(debug=True)
