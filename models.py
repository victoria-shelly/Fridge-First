from datetime import date
class FoodItem:
    def __init__(self, name, expires, price=0):
        self.name = name.strip().lower() # Normalizes the name
        self.expires = date.fromisoformat(expires) # Convertes text to a date object
        self.price = price
    def days_left(self, today):
    return (self.expires - today).days # Calculates the number of days left until expiration

    def status(self, today):
        days_left = self.days_left(today)
        if days_left < 0:
            return "expired"
            elif days_left == 0:
                return "red"
            elif days_left >= 1 and days_left <=3:
                return "yellow"
            else:
                return "green" 
    def to_dict(self, today):
    # Converts the object to a dictionary for JSON serialization. 
    # Quotes are used for the keys to ensure they are strings.
        return {
            "name": self.name, 
            "expires": self.expires.isoformat(),
            "price": self.price,
            "days_left": self.days_left(today),
            "status": self.status(today) 
            
        }
    def __repr__(self):
        return f"FoodItem(name={self.name}, expires={self.expires}, price={self.price})"
        # This method provides a string representation of the object, useful for debugging and logging.

class Recipe:
    def __init__(self, name, ingredients, steps):
       self.name = name
       self.ingredients = {ing.strip().lower() for ing in ingredients} # Normalizes the ingredients
       self.steps = steps #List of steps to prepare the recipe
    def to_dict(self):
        return {
            "name": self.name,
            "ingredients": sorted(self.ingredients), # Sorts the ingredients for consistent ordering
            "steps": self.steps
        }
    @classmethod #Allows the method to be called on the class itself, rather than on an instance of the class. 
    #This is useful for creating instances from data without needing an existing instance.
    def from_dict(cls, data):
        return cls(
            name=data["name"],
            ingredients=data["ingredients"],
            steps=data["steps"]
        )
    def can_make(self, pantry_items):
        return self.ingredients.issubset(pantry_items)  # Checks available items