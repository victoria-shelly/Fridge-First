"""Data-model role: SQLite helpers with parameterized queries only."""

from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path

from models import FoodItem, Recipe, normalize_name, parse_date

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "fridge.db"
RECIPES_PATH = ROOT / "recipes.json"
INGREDIENTS_PATH = ROOT / "ingredients.json"

SAMPLE_FRIDGE = [
    ("chicken", "2026-11-14"),
    ("bell pepper", "2026-11-16"),
    ("yogurt", "2026-11-19"),
    ("eggs", "2026-11-25"),
    ("rice", "2027-03-01"),
    ("bread", "2026-11-13"),
    ("onion", "2026-11-18"),
    ("cheese", "2026-11-22"),
]


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                expires_on TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS custom_recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                ingredients_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS impact_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL CHECK (kind IN ('saved', 'wasted')),
                item_name TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS shopping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );
            """
        )


def load_builtin_recipes() -> list[Recipe]:
    data = json.loads(RECIPES_PATH.read_text(encoding="utf-8"))
    return [Recipe.from_mapping(row, custom=False) for row in data]


def load_ingredients() -> list[str]:
    data = json.loads(INGREDIENTS_PATH.read_text(encoding="utf-8"))
    return sorted({normalize_name(x) for x in data})


def list_items() -> list[FoodItem]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, name, expires_on FROM items ORDER BY expires_on ASC, name ASC"
        ).fetchall()
    return [
        FoodItem(id=row["id"], name=row["name"], expires_on=parse_date(row["expires_on"]))
        for row in rows
    ]


def add_item(name: str, expires_on: str | date) -> FoodItem:
    item = FoodItem(name=name, expires_on=parse_date(expires_on))
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO items (name, expires_on) VALUES (?, ?)",
            (item.name, item.expires_on.isoformat()),
        )
        item.id = int(cur.lastrowid)
    return item


def delete_item(item_id: int) -> FoodItem | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT id, name, expires_on FROM items WHERE id = ?",
            (item_id,),
        ).fetchone()
        if row is None:
            return None
        conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
    return FoodItem(id=row["id"], name=row["name"], expires_on=parse_date(row["expires_on"]))


def clear_items() -> None:
    with connect() as conn:
        conn.execute("DELETE FROM items")


def load_sample_fridge() -> list[FoodItem]:
    clear_items()
    return [add_item(name, expires) for name, expires in SAMPLE_FRIDGE]


def list_custom_recipes() -> list[Recipe]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, name, ingredients_json FROM custom_recipes ORDER BY name ASC"
        ).fetchall()
    recipes: list[Recipe] = []
    for row in rows:
        ingredients = json.loads(row["ingredients_json"])
        recipes.append(
            Recipe(
                id=row["id"],
                name=row["name"],
                ingredients=set(ingredients),
                custom=True,
            )
        )
    return recipes


def add_custom_recipe(name: str, ingredients: list[str]) -> Recipe:
    recipe = Recipe(name=name, ingredients=set(ingredients), custom=True)
    payload = json.dumps(sorted(recipe.ingredients))
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO custom_recipes (name, ingredients_json) VALUES (?, ?)",
            (recipe.name, payload),
        )
        recipe.id = int(cur.lastrowid)
    return recipe


def all_recipes() -> list[Recipe]:
    return load_builtin_recipes() + list_custom_recipes()


def log_impact(kind: str, item_name: str, when: date | str | None = None) -> None:
    stamp = parse_date(when or date.today()).isoformat()
    with connect() as conn:
        conn.execute(
            "INSERT INTO impact_log (kind, item_name, created_at) VALUES (?, ?, ?)",
            (kind, normalize_name(item_name), stamp),
        )


def impact_counts() -> dict[str, int]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT kind, COUNT(*) AS n FROM impact_log GROUP BY kind"
        ).fetchall()
    counts = {"saved": 0, "wasted": 0}
    for row in rows:
        counts[row["kind"]] = int(row["n"])
    return counts


def add_shopping_items(names: list[str]) -> list[str]:
    cleaned = sorted({normalize_name(n) for n in names if str(n).strip()})
    with connect() as conn:
        for name in cleaned:
            conn.execute(
                "INSERT OR IGNORE INTO shopping (name) VALUES (?)",
                (name,),
            )
    return list_shopping()


def list_shopping() -> list[str]:
    with connect() as conn:
        rows = conn.execute("SELECT name FROM shopping ORDER BY name ASC").fetchall()
    return [row["name"] for row in rows]


def clear_shopping() -> None:
    with connect() as conn:
        conn.execute("DELETE FROM shopping")
