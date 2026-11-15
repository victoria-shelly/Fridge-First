"""Data-model: FoodItem and Recipe."""

from __future__ import annotations

from datetime import date, datetime


def parse_date(value: str | date | datetime) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value).strip()[:10])


def normalize_name(name: str) -> str:
    return " ".join(str(name).strip().lower().split())


class FoodItem:
    def __init__(self, name, expires, price=0, item_id=None, state="active"):
        self.id = item_id
        self.name = normalize_name(name)
        self.expires = parse_date(expires)
        self.price = float(price or 0)
        self.state = state

    def days_left(self, today):
        return (self.expires - parse_date(today)).days

    def status(self, today):
        days = self.days_left(today)
        if days < 0:
            return "gray"
        if days == 0:
            return "red"
        if days <= 3:
            return "yellow"
        return "green"

    def urgency_points(self, today):
        return {"red": 10, "yellow": 5, "green": 1, "gray": 0}[self.status(today)]

    def to_dict(self, today):
        color = self.status(today)
        return {
            "id": self.id,
            "name": self.name,
            "expires": self.expires.isoformat(),
            "expires_on": self.expires.isoformat(),
            "price": self.price,
            "days_left": self.days_left(today),
            "status": color,
            "color": color,
            "urgency_points": self.urgency_points(today),
            "state": self.state,
        }

    def __getitem__(self, key):
        # Allow dict-style access used by some teammate tests.
        mapping = {
            "id": self.id,
            "name": self.name,
            "expires": self.expires.isoformat(),
            "price": self.price,
            "state": self.state,
        }
        if key not in mapping:
            raise KeyError(key)
        return mapping[key]

    def __repr__(self):
        return f"FoodItem(name={self.name!r}, expires={self.expires}, price={self.price})"


class Recipe:
    def __init__(self, name, ingredients, steps=None, recipe_id=None):
        self.id = recipe_id
        self.name = str(name).strip()
        self.ingredients = {normalize_name(ing) for ing in ingredients if str(ing).strip()}
        self.steps = list(steps or [])

    def can_make(self, pantry_items):
        pantry = {normalize_name(x) for x in pantry_items}
        return self.ingredients.issubset(pantry)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "ingredients": sorted(self.ingredients),
            "steps": self.steps,
        }

    def __getitem__(self, key):
        data = self.to_dict()
        if key == "ingredients":
            return sorted(self.ingredients)
        if key not in data:
            raise KeyError(key)
        return data[key]

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data["name"],
            ingredients=data.get("ingredients", []),
            steps=data.get("steps", []),
            recipe_id=data.get("id"),
        )
