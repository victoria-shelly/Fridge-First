"""Frontend + security role: validate and sanitize user input."""

from __future__ import annotations

import re
from datetime import date
from html import escape

from models import normalize_name

MAX_NAME_LEN = 80
MAX_INGREDIENTS = 20
ALLOWED_NAME = re.compile(r"^[A-Za-z0-9 \-_',.&()/]+$")

# Simple in-memory rate limit for add endpoints.
_rate_buckets: dict[str, list[float]] = {}
RATE_LIMIT = 20
RATE_WINDOW_SECONDS = 60


def plain_text(value: str) -> str:
    """Always treat user content as text — never as HTML/JS."""
    return escape(str(value), quote=True)


def validate_name(raw: str, field: str = "name") -> str:
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


def validate_date(raw: str) -> str:
    if raw is None or not str(raw).strip():
        raise ValueError("expires_on is required")
    text = str(raw).strip()
    try:
        parsed = date.fromisoformat(text[:10])
    except ValueError as exc:
        raise ValueError("expires_on must be YYYY-MM-DD") from exc
    if parsed.year < 2000 or parsed.year > 2100:
        raise ValueError("expires_on year out of range")
    return parsed.isoformat()


def validate_today(raw: str | None) -> str:
    if raw is None or not str(raw).strip():
        return date.today().isoformat()
    return validate_date(raw)


def validate_ingredients(raw: list | None) -> list[str]:
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


def check_rate_limit(bucket: str, now: float | None = None) -> None:
    import time

    stamp = time.time() if now is None else now
    window = _rate_buckets.setdefault(bucket, [])
    cutoff = stamp - RATE_WINDOW_SECONDS
    alive = [t for t in window if t >= cutoff]
    if len(alive) >= RATE_LIMIT:
        _rate_buckets[bucket] = alive
        raise ValueError("rate limit exceeded; try again in a minute")
    alive.append(stamp)
    _rate_buckets[bucket] = alive


def security_headers() -> dict[str, str]:
    return {
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "object-src 'none'; "
            "base-uri 'self'"
        ),
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
    }
