def normalize(name):
    return name.strip().lower()


def build_shopping_list(chosen_recipes, fridge_names):
    fridge_set = {normalize(name) for name in fridge_names}
    new_dict = {}
    
    for recipe in chosen_recipes:
        recipe_set = {normalize(ingredient) for ingredient in recipe["ingredients"]}
        
        missing_items = recipe_set - fridge_set
        for item in missing_items:
            item += recipe["name"]
            
            if item not in new_dict:
                new_dict[item] = []
            new_dict[item].append(recipe["name"])
            
    result = []
    for item in sorted(new_dict):
         result.append({"item": item, "for_recipes": sorted(new_dict[item])})
    return result
                
                
        
        