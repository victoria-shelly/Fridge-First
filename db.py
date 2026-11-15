import json
import sqlite3
from models import FoodItem, Recipe

def init_db():
    conn = sqlite3.connect('fridge.db')
    conn.row_factory = sqlite3.Row

#Items table
conn.execute("""
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    expires TEXT,
    price REAL,
    state TEXT
)
""")

#Custom Recipes table
conn.execute("""
CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    ingredients TEXT,
    steps TEXT
)
""")

#Log table
conn.execute("""
    CREATE TABLE IF NOT EXISTS log(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    status TEXT,
    date TEXT,
    price REAL
    )
""")
conn.commit()
conn.close()

def add_item(name, expires, price=0, state="active"):
    name = name.strip() # Normalize the name by stripping whitespace
    conn = sqlite3.connect('fridge.db')
    conn.execute(
        "INSERT INTO items (name, expires, price, state) VALUES (?, ?, ?, ?)", 
    (name, expires, price, state)
    )
    conn.commit()
    conn.close()

def list_active_items():
    conn = sqlite3.connect('fridge.db')
    conn.row_factory = sqlite3.Row # Enable dictionary-style lookups
    cursor = conn.execute("SELECT * FROM items WHERE state='active'")
    items = cursor.fetchall()
    conn.close()
    return[
        FoodItem(row["name"], row["expires"], row["price"]) 
        for row in items
    ]

def mark_used(names, today):
    conn = sqlite3.connect('fridge.db')
    conn.row_factory = sqlite3.Row
    for name in names:
        # Fetch the price of the active item 
        name = name.strip().lower() # Match FoodItem normalization
        cursor = conn.execute(
            "SELECT price FROM items WHERE name = ? AND state = 'active'", 
            (name,)
        )
        item = cursor.fetchone()
        if item:
            price = item["price"]
            # Update the item state to 'used' 
            conn.execute(
                "UPDATE items SET state = 'used' WHERE name = ? AND state = 'active'", 
                (name,)
            )
            # Log the saved item 
            conn.execute(
                "INSERT INTO log (name, status, date, price) VALUES (?, 'saved', ?, ?)",
                (name, today, price)
            )
    conn.commit()
    conn.close()

def throw_out(item_id, today):
    conn = sqlite3.connect('fridge.db')
    conn.row_factory = sqlite3.Row
    
    # Fetch the name and price of the item to be thrown out
    cursor = conn.execute("SELECT name, price FROM items WHERE id = ?", (item_id,))
    item = cursor.fetchone()
    
    if item:
        name = item["name"]
        price = item["price"]
        
        # 2. Update state to 'wasted' 
        conn.execute("UPDATE items SET state = 'wasted' WHERE id = ?", (item_id,))
        
        # 3. Log the wasted item 
        conn.execute(
            "INSERT INTO log (name, status, date, price) VALUES (?, 'wasted', ?, ?)",
            (name, today, price)
        )
        
    conn.commit()
    conn.close()


def add_recipe(name, ingredients, steps):
    conn = sqlite3.connect('fridge.db')
    conn.execute(
        "INSERT INTO recipes (name, ingredients, steps) VALUES (?, ?, ?)",
        (name, json.dumps(ingredients), json.dumps(steps))
    )
    conn.commit()
    conn.close()
    
def list_recipes():
    conn = sqlite3.connect('fridge.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT * FROM recipes")
    rows = cursor.fetchall()
    conn.close()
    recipes = []
    for row in rows:
        recipe_dict={
            "name": row["name"],
            "ingredients": json.loads(row["ingredients"]),
            "steps": json.loads(row["steps"])
        }
        recipes.append(Recipe.from_dict(recipe_dict)) # changed to Recipe.from_dict to create Recipe instances from the dictionary representation
    return recipes

def get_log():
    conn = sqlite3.connect('fridge.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT * FROM log")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_available_recipes():
    # Fetch active fridge items and all recipes 
    active_items = list_active_items()
    all_recipes = list_recipes()
    
    # Extract item names from FoodItem objects 
    active_names = {item.name for item in active_items}
    # Use the Recipe model's built-in can_make method 
    return [recipe for recipe in all_recipes if recipe.can_name(active_names) or recipe.can_make(active_names)]