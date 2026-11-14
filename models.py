"""Data-model role: FoodItem and Recipe classes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Iterable


def parse_date(value: str | date) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    return date.fromisoformat(str(value)[:10])


def normalize_name(name: str) -> str:
    return " ".join(str(name).strip().lower().split())


@dataclass
class FoodItem:
    name: str
    expires_on: date
    id: int | None = None

    def __post_init__(self) -> None:
        self.name = normalize_name(self.name)
        self.expires_on = parse_date(self.expires_on)

    def days_left(self, today: date | str) -> int:
        return (self.expires_on - parse_date(today)).days

    def status(self, today: date | str) -> str:
        days = self.days_left(today)
        if days < 0:
            return "gray"
        if days == 0:
            return "red"
        if days <= 3:
            return "yellow"
        return "green"

    def urgency_points(self, today: date | str) -> int:
        return {"red": 10, "yellow": 5, "green": 1, "gray": 0}[self.status(today)]

    def to_dict(self, today: date | str) -> dict:
        color = self.status(today)
        return {
            "id": self.id,
            "name": self.name,
            "expires_on": self.expires_on.isoformat(),
            "days_left": self.days_left(today),
            "color": color,
            "urgency_points": self.urgency_points(today),
        }


@dataclass
class Recipe:
    name: str
    ingredients: set[str] = field(default_factory=set)
    custom: bool = False
    id: int | None = None

    def __post_init__(self) -> None:
        self.name = str(self.name).strip()
        self.ingredients = {normalize_name(i) for i in self.ingredients if str(i).strip()}

    @classmethod
    def from_mapping(cls, data: dict, custom: bool = False) -> "Recipe":
        return cls(
            name=data["name"],
            ingredients=set(data.get("ingredients", [])),
            custom=custom,
            id=data.get("id"),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "ingredients": sorted(self.ingredients),
            "custom": self.custom,
        }


def recipes_from_iterable(rows: Iterable[dict], custom: bool = False) -> list[Recipe]:
    return [Recipe.from_mapping(row, custom=custom) for row in rows]
