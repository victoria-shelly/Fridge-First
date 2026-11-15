"""Impact stats: saved vs wasted and estimated money saved."""

from __future__ import annotations

from datetime import timedelta


def build_stats(entries, today=None, days=7):
    if not entries:
        empty = {
            "saved": 0,
            "wasted": 0,
            "money_saved": 0.0,
            "saved_count": 0,
            "wasted_count": 0,
            "estimated_money_saved": 0.0,
            "by_day": [],
        }
        return empty

    saved_entries = 0
    wasted_entries = 0
    money = 0.0
    for entry in entries:
        status = entry["status"] if not isinstance(entry, str) else None
        if hasattr(entry, "keys"):
            status = entry["status"]
            price = entry["price"] if "price" in entry.keys() else 0
        else:
            status = entry.get("status")
            price = entry.get("price", 0)

        if status == "saved":
            saved_entries += 1
            money += float(price or 0)
        elif status == "wasted":
            wasted_entries += 1

    payload = {
        "saved": saved_entries,
        "wasted": wasted_entries,
        "money_saved": round(money, 2),
        "saved_count": saved_entries,
        "wasted_count": wasted_entries,
        "estimated_money_saved": round(money, 2),
    }
    if today is not None:
        payload["by_day"] = daily_breakdown(entries, today, days)
    else:
        payload["by_day"] = []
    return payload


def daily_breakdown(entries, today, days=7):
    counts = {}
    day_texts = []
    for day in range(days - 1, -1, -1):
        date_num = today - timedelta(days=day)
        date_text = date_num.isoformat()
        day_texts.append(date_text)
        counts[date_text] = {"saved": 0, "wasted": 0}

    for entry in entries:
        day = entry["date"]
        status = entry["status"]
        if day in counts and status in counts[day]:
            counts[day][status] += 1

    return [
        {"date": text, "saved": counts[text]["saved"], "wasted": counts[text]["wasted"]}
        for text in day_texts
    ]
