"""Input validation and output escaping."""

from __future__ import annotations

import re
from datetime import date
from html import escape

from models import normalize_name

MAX_NAME_LEN = 80
MAX_INGREDIENTS = 20
ALLOWED_NAME = re.compile(r"^[A-Za-z0-9 \-_',.&()/]+$")


def plain_text(value: str) -> str:
    return escape(str(value), quote=True)


def validate_name(raw, field="name"):
    if raw is None:
        raise ValueError(f"{field} is required")
    name = normalize_name(raw)
    if not name:
        raise ValueError(f"{field} is required")
    if len(name) > MAX_NAME_LEN:
        raise ValueError(f"{field} must be at most {MAX_NAME_LEN} characters")
    if not ALLOWED_NAME.match(name):
        raise ValueError(f"{field} has invalid characters")
    return name


def validate_date(raw, field="expires_on"):
    if raw is None or not str(raw).strip():
        raise ValueError(f"{field} is required")
    try:
        parsed = date.fromisoformat(str(raw).strip()[:10])
    except ValueError as exc:
        raise ValueError(f"{field} must be YYYY-MM-DD") from exc
    if parsed.year < 2000 or parsed.year > 2100:
        raise ValueError(f"{field} year out of range")
    return parsed.isoformat()


def validate_today(raw=None):
    if raw is None or not str(raw).strip():
        return date.today().isoformat()
    return validate_date(raw, field="today")


def validate_ingredients(raw):
    if not isinstance(raw, list) or not raw:
        raise ValueError("ingredients must be a non-empty list")
    if len(raw) > MAX_INGREDIENTS:
        raise ValueError(f"at most {MAX_INGREDIENTS} ingredients")
    cleaned = []
    seen = set()
    for item in raw:
        name = validate_name(item, field="ingredient")
        if name not in seen:
            cleaned.append(name)
            seen.add(name)
    return cleaned


def validate_item(data: dict) -> list[str]:
    issues = []
    try:
        validate_name(data.get("name"))
    except ValueError as exc:
        issues.append(str(exc))
    expires = data.get("expires_on", data.get("expires"))
    try:
        validate_date(expires)
    except ValueError as exc:
        issues.append(str(exc))
    return issues


def validate_recipe(data: dict) -> list[str]:
    issues = []
    try:
        validate_name(data.get("name"), field="recipe name")
    except ValueError as exc:
        issues.append(str(exc))
    try:
        validate_ingredients(data.get("ingredients"))
    except ValueError as exc:
        issues.append(str(exc))
    return issues


def security_headers():
    return {
        "Content-Security-Policy": (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; object-src 'none'; base-uri 'self'"
        ),
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
    }
