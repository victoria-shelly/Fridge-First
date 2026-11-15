"""SQLite helpers with parameterized queries only."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from models import FoodItem, Recipe, normalize_name, parse_date

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "fridge.db"
RECIPES_PATH = ROOT / "recipes.json"
INGREDIENTS_PATH = ROOT / "ingredients.json"

SAMPLE_FRIDGE = [
    ("chicken", "2026-11-14", 6.0),
    ("bell pepper", "2026-11-16", 1.5),
    ("yogurt", "2026-11-19", 2.0),
    ("eggs", "2026-11-25", 3.0),
    ("rice", "2027-03-01", 2.5),
    ("bread", "2026-11-13", 2.0),
    ("onion", "2026-11-18", 1.0),
    ("cheese", "2026-11-22", 3.5),
]


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                expires TEXT NOT NULL,
                price REAL DEFAULT 0,
                state TEXT NOT NULL DEFAULT 'active'
            );
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                ingredients TEXT NOT NULL,
                steps TEXT NOT NULL DEFAULT '[]',
                source TEXT NOT NULL DEFAULT 'custom'
            );
            CREATE TABLE IF NOT EXISTS log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                status TEXT NOT NULL,
                date TEXT NOT NULL,
                price REAL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS shopping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );
            """
        )
    seed_builtin_recipes()


def seed_builtin_recipes():
    """No-op: cookbook recipes are read live from recipes.json, not copied into SQLite."""
    return


def load_json_recipes() -> list[Recipe]:
    """Voyage cookbook — always from recipes.json only."""
    if not RECIPES_PATH.exists():
        return []
    data = json.loads(RECIPES_PATH.read_text(encoding="utf-8"))
    recipes = []
    for index, row in enumerate(data):
        recipes.append(
            Recipe(
                name=row["name"],
                ingredients=row.get("ingredients", []),
                steps=row.get("steps", []),
                recipe_id=f"json-{index}",
            )
        )
    return recipes


def load_ingredients():
    if not INGREDIENTS_PATH.exists():
        return []
    data = json.loads(INGREDIENTS_PATH.read_text(encoding="utf-8"))
    return sorted({normalize_name(x) for x in data})


def add_item(name, expires, price=0, state="active"):
    item = FoodItem(name=name, expires=expires, price=price, state=state)
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO items (name, expires, price, state) VALUES (?, ?, ?, ?)",
            (item.name, item.expires.isoformat(), item.price, item.state),
        )
        item.id = int(cur.lastrowid)
    return item


def list_active_items():
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, name, expires, price, state FROM items WHERE state = 'active' ORDER BY expires ASC, name ASC"
        ).fetchall()
    return [
        FoodItem(
            name=row["name"],
            expires=row["expires"],
            price=row["price"],
            item_id=row["id"],
            state=row["state"],
        )
        for row in rows
    ]


def clear_active_items():
    with connect() as conn:
        conn.execute("DELETE FROM items WHERE state = 'active'")


def load_sample_fridge():
    clear_active_items()
    return [add_item(name, expires, price) for name, expires, price in SAMPLE_FRIDGE]


def mark_used(names, today):
    today_text = parse_date(today).isoformat()
    removed = []
    with connect() as conn:
        for raw in names:
            name = normalize_name(raw)
            row = conn.execute(
                "SELECT id, name, price FROM items WHERE name = ? AND state = 'active' ORDER BY expires ASC LIMIT 1",
                (name,),
            ).fetchone()
            if not row:
                continue
            conn.execute("UPDATE items SET state = 'used' WHERE id = ?", (row["id"],))
            conn.execute(
                "INSERT INTO log (name, status, date, price) VALUES (?, 'saved', ?, ?)",
                (row["name"], today_text, row["price"]),
            )
            removed.append(row["name"])
    return removed


def throw_out(item_id, today=None):
    today_text = parse_date(today or date_today()).isoformat()
    with connect() as conn:
        row = conn.execute(
            "SELECT id, name, price, state FROM items WHERE id = ?",
            (item_id,),
        ).fetchone()
        if row is None or row["state"] != "active":
            return False
        conn.execute("UPDATE items SET state = 'wasted' WHERE id = ?", (item_id,))
        conn.execute(
            "INSERT INTO log (name, status, date, price) VALUES (?, 'wasted', ?, ?)",
            (row["name"], today_text, row["price"]),
        )
    return True


def date_today():
    from datetime import date

    return date.today()


def add_recipe(name, ingredients, steps=None):
    recipe = Recipe(name=name, ingredients=ingredients, steps=steps or [])
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO recipes (name, ingredients, steps, source) VALUES (?, ?, ?, 'custom')",
            (recipe.name, json.dumps(sorted(recipe.ingredients)), json.dumps(recipe.steps)),
        )
        recipe.id = int(cur.lastrowid)
    return recipe


def list_custom_recipes():
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, name, ingredients, steps FROM recipes WHERE source = 'custom' ORDER BY name ASC"
        ).fetchall()
    recipes = []
    for row in rows:
        recipes.append(
            Recipe(
                name=row["name"],
                ingredients=json.loads(row["ingredients"]),
                steps=json.loads(row["steps"] or "[]"),
                recipe_id=row["id"],
            )
        )
    return recipes


def list_recipes():
    """Displayed / ranked cookbook comes only from recipes.json."""
    return load_json_recipes()


def find_recipe_by_name(name: str):
    needle = str(name).strip().lower()
    for recipe in load_json_recipes():
        if recipe.name.strip().lower() == needle:
            return recipe
    for recipe in list_custom_recipes():
        if recipe.name.strip().lower() == needle:
            return recipe
    return None


def get_log():
    with connect() as conn:
        rows = conn.execute("SELECT name, status, date, price FROM log").fetchall()
    return [dict(row) for row in rows]


def add_shopping_items(names):
    cleaned = sorted({normalize_name(n) for n in names if str(n).strip()})
    with connect() as conn:
        for name in cleaned:
            conn.execute("INSERT OR IGNORE INTO shopping (name) VALUES (?)", (name,))
    return list_shopping()


def list_shopping():
    with connect() as conn:
        rows = conn.execute("SELECT name FROM shopping ORDER BY name ASC").fetchall()
    return [row["name"] for row in rows]


def get_available_recipes():
    active_names = {item.name for item in list_active_items()}
    return [recipe for recipe in load_json_recipes() if recipe.can_make(active_names)]
