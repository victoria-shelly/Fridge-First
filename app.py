"""Python role: Flask routes and wiring everyone else's modules together."""

from __future__ import annotations

from flask import Flask, jsonify, render_template, request

import db
import ranking
import security
import shopping
import stats

app = Flask(__name__)
db.init_db()


@app.after_request
def apply_security_headers(response):
    for key, value in security.security_headers().items():
        response.headers[key] = value
    return response


def _error(message: str, code: int = 400):
    return jsonify({"error": message}), code


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/api/ingredients")
def api_ingredients():
    return jsonify(db.load_ingredients())


@app.get("/api/items")
def api_list_items():
    try:
        today = security.validate_today(request.args.get("today"))
    except ValueError as exc:
        return _error(str(exc))
    items = [item.to_dict(today) for item in db.list_items()]
    order = {"red": 0, "yellow": 1, "green": 2, "gray": 3}
    items.sort(key=lambda row: (order[row["color"]], row["days_left"], row["name"]))
    return jsonify({"today": today, "items": items})


@app.post("/api/items")
def api_add_item():
    payload = request.get_json(silent=True) or {}
    try:
        security.check_rate_limit("add-item")
        name = security.validate_name(payload.get("name"))
        expires_on = security.validate_date(payload.get("expires_on"))
        today = security.validate_today(payload.get("today"))
    except ValueError as exc:
        return _error(str(exc))
    item = db.add_item(name, expires_on)
    return jsonify(item.to_dict(today)), 201


@app.post("/api/items/<int:item_id>/throw")
def api_throw_item(item_id: int):
    payload = request.get_json(silent=True) or {}
    try:
        today = security.validate_today(payload.get("today") or request.args.get("today"))
    except ValueError as exc:
        return _error(str(exc))
    item = db.delete_item(item_id)
    if item is None:
        return _error("item not found", 404)
    stats.record_wasted(item.name, today)
    return jsonify({"thrown": item.to_dict(today), "stats": stats.get_stats()})


@app.post("/api/sample-fridge")
def api_sample_fridge():
    payload = request.get_json(silent=True) or {}
    try:
        today = security.validate_today(payload.get("today"))
    except ValueError as exc:
        return _error(str(exc))
    items = [item.to_dict(today) for item in db.load_sample_fridge()]
    return jsonify({"today": today, "items": items})


@app.get("/api/recipes")
def api_list_recipes():
    return jsonify([recipe.to_dict() for recipe in db.all_recipes()])


@app.post("/api/recipes")
def api_add_recipe():
    payload = request.get_json(silent=True) or {}
    try:
        security.check_rate_limit("add-recipe")
        name = security.validate_name(payload.get("name"), field="recipe name")
        ingredients = security.validate_ingredients(payload.get("ingredients"))
    except ValueError as exc:
        return _error(str(exc))
    recipe = db.add_custom_recipe(name, ingredients)
    return jsonify(recipe.to_dict()), 201


@app.get("/api/rank")
def api_rank():
    try:
        today = security.validate_today(request.args.get("today"))
    except ValueError as exc:
        return _error(str(exc))
    ranked = ranking.rank_recipes(db.all_recipes(), db.list_items(), today)
    return jsonify({"today": today, "recipes": ranked})


@app.get("/api/this-week")
def api_this_week():
    try:
        today = security.validate_today(request.args.get("today"))
    except ValueError as exc:
        return _error(str(exc))
    plan = ranking.this_week_plan(db.all_recipes(), db.list_items(), today)
    return jsonify({"today": today, "plan": plan})


@app.post("/api/cook")
def api_cook():
    payload = request.get_json(silent=True) or {}
    try:
        today = security.validate_today(payload.get("today"))
        recipe_name = security.validate_name(payload.get("recipe_name"), field="recipe_name")
    except ValueError as exc:
        return _error(str(exc))

    recipe = next(
        (r for r in db.all_recipes() if r.name.strip().lower() == recipe_name),
        None,
    )
    if recipe is None:
        return _error("recipe not found", 404)

    matched = ranking.match_recipe(recipe, db.list_items(), today)
    used_names = {u["name"] for u in matched["uses"]}
    removed = []
    for item in list(db.list_items()):
        if item.name in used_names and item.id is not None:
            deleted = db.delete_item(item.id)
            if deleted is not None:
                removed.append(deleted.name)
                used_names.discard(item.name)

    stats.record_saved(removed, today)
    shopping_list = shopping.add_from_missing(matched["missing"])
    return jsonify(
        {
            "recipe": matched["name"],
            "removed": removed,
            "missing_added": matched["missing"],
            "shopping_list": shopping_list,
            "stats": stats.get_stats(),
        }
    )


@app.get("/api/shopping-list")
def api_shopping_list():
    return jsonify({"items": shopping.get_list()})


@app.get("/api/stats")
def api_stats():
    return jsonify(stats.get_stats())


if __name__ == "__main__":
    app.run(debug=True, port=5000)
