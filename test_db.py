import sqlite3
from datetime import date

import pytest

from db import (
    add_item,
    add_recipe,
    get_available_recipes,
    get_log,
    init_db,
    list_active_items,
    list_recipes,
    mark_used,
    throw_out,
)


@pytest.fixture
def db_fixture(monkeypatch, tmp_path):
    db_path = tmp_path / "test.db"

    def _connect():
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    monkeypatch.setattr("db.connect", _connect)
    monkeypatch.setattr("db.DB_PATH", db_path)
    init_db()
    yield db_path


def test_add_and_list_item(db_fixture):
    add_item("apple", "2026-11-20", 1.00)
    items = list_active_items()
    assert len(items) == 1
    assert items[0]["name"] == "apple"
    assert items[0]["price"] == 1.00
    assert items[0]["id"] is not None


def test_sql_injection_safety(db_fixture):
    malicious_name = "drop table items"
    add_item(malicious_name, "2026-11-25", 2.00)
    items = list_active_items()
    assert len(items) == 1
    assert items[0]["name"] == malicious_name


def test_name_normalization(db_fixture):
    add_item(" Chicken ", "2026-11-20", 3.00)
    items = list_active_items()
    assert len(items) == 1
    assert items[0]["name"] == "chicken"


def test_mark_used(db_fixture):
    add_item("flour", "2026-11-30", 2.00)
    add_item("milk", "2026-11-20", 1.50)
    add_item("eggs", "2026-11-25", 3.00)
    add_recipe("Pancakes", ["flour", "milk", "eggs"], ["Mix", "Cook"])

    removed = mark_used(["flour", "milk", "eggs"], date(2026, 11, 14))
    assert set(removed) == {"flour", "milk", "eggs"}
    assert list_active_items() == []
    log = get_log()
    assert len(log) == 3
    assert all(entry["status"] == "saved" for entry in log)


def test_throw_out(db_fixture):
    add_item("yogurt", "2026-11-20", 1.50)
    item_id = list_active_items()[0]["id"]
    assert throw_out(item_id, date(2026, 11, 14)) is True
    assert list_active_items() == []
    assert get_log()[0]["status"] == "wasted"


def test_get_available_recipes(db_fixture):
    add_item("flour", "2026-11-30", 2.00)
    add_item("milk", "2026-11-20", 1.50)
    add_item("eggs", "2026-11-25", 3.00)
    add_recipe("Pancakes", ["flour", "milk", "eggs"], ["Mix", "Cook"])
    add_recipe("Toast", ["bread"], ["Toast it"])
    available = get_available_recipes()
    assert [r.name for r in available] == ["Pancakes"]
    assert list_recipes()  # seeded builtins + customs exist
