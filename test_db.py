import sqlite3
from datetime import date
import pytest
from db import init_db, add_item, add_recipe, list_active_items, list_recipes, mark_used, throw_out, get_log, get_available_recipes

@pytest.fixture
def db_fixture(monkeypatch):
    conn = sqlite3.connect(":memory:")  # Use an in-memory database for testing
    conn.row_factory = sqlite3.Row

    # Patch the sqlite3.connect method to return our in-memory connection in db.py functions
    monkeypatch.setattr("db.sqlite3.connect", lambda *args, **kwargs: conn)
    # Initialize the database
    init_db()
    
    yield conn # This allows the test to run

    conn.close()

def test_add_and_list_item(db_fixture):
    # 1. Add an active item 
    add_item("apple", "2026-11-20", 1.00)
    
    # 2. Retrieve active items 
    items = list_active_items()
    
    # 3. Assert the item was stored correctly
    assert len(items) == 1
    assert items[0]["name"] == "apple"
    assert items[0]["price"] == 1.00
    
def test_sql_injection_safety(db_fixture):
    malicious_name = "'); DROP TABLE items;--"
    
    # 1. Add the malicious string as an item name
    add_item(malicious_name, "2026-11-25", 2.00)
    
    # 2. Verify the table is intact and the string was stored literally 📝
    items = list_active_items()
    assert len(items) == 1
    assert items[0]["name"] == malicious_name

def test_name_normalization(db_fixture):
    # 1. Add an item with extra spaces and uppercase letters 🐔
    add_item(" Chicken ", "2026-11-20", 3.00)
    
    # 2. Retrieve active items and check normalization 📝
    items = list_active_items()
    assert len(items) == 1
    assert items[0]["name"] == "chicken"

def test_mark_used(db_fixture):
    # 1. Add pantry items required for pancakes 🥞
    add_item("flour", "2026-11-30", 2.00)
    add_item("milk", "2026-11-20", 1.50)
    add_item("eggs", "2026-11-25", 3.00)
    
    # 2. Add the recipe 
    add_recipe("Pancakes", ["flour", "milk", "eggs"], ["Mix", "Cook"])
    
    # 3. Mark the recipe as used 
    mark_used("Pancakes")
    
    # 4. Verify that active items are removed from the pantry 
    items = list_active_items()
    assert len(items) == 0

def test_throw_out(db_fixture):
    # 1. Add an item to the pantry 
    add_item("yogurt", "2026-11-20", 1.50)
    
    # 2. Retrieve the item ID 
    items = list_active_items()
    item_id = items[0]["id"]
    
    # 3. Throw out the item 
    throw_out(item_id)
    
    # 4. Verify that the item is no longer active 
    items_after = list_active_items()
    assert len(items_after) == 0
    
    # 5. Check the log for the wasted entry 
    log_entries = get_log()
    assert any(entry["name"] == "yogurt" and entry["status"] == "wasted" for entry in log_entries)