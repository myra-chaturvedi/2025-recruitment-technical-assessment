from dataclasses import dataclass
from typing import List, Dict, Union
from flask import Flask, request, jsonify
import re

# ==== Type Definitions, feel free to add or modify ===========================
@dataclass
class CookbookEntry:
	name: str

@dataclass
class RequiredItem():
	name: str
	quantity: int

@dataclass
class Recipe(CookbookEntry):
	required_items: List[RequiredItem]

@dataclass
class Ingredient(CookbookEntry):
	cook_time: int


# =============================================================================
# ==== HTTP Endpoint Stubs ====================================================
# =============================================================================
app = Flask(__name__)

# Store your recipes here!
cookbook = {}

# Task 1 helper (don't touch)
@app.route("/parse", methods=['POST'])
def parse():
	data = request.get_json()
	recipe_name = data.get('input', '')
	parsed_name = parse_handwriting(recipe_name)
	if parsed_name is None:
		return 'Invalid recipe name', 400
	return jsonify({'msg': parsed_name}), 200

# [TASK 1] ====================================================================
# Takes in a recipeName and returns it in a form that 
def parse_handwriting(recipeName: str) -> Union[str | None]:
	if not recipeName or not isinstance(recipeName, str):
		return None
	
	parsed = re.sub(r'[-_]', ' ', recipeName)
	parsed = re.sub(r'[^a-zA-Z ]', '', parsed)
	parsed = re.sub(r'\s+', ' ', parsed).strip()
	parsed = parsed.title()

	return parsed if parsed else None #if string is empty post improving it, then we can just return none
	return recipeName

# [TASK 2] ====================================================================
# Endpoint that adds a CookbookEntry to your magical cookbook
@app.route('/entry', methods=['POST'])
def create_entry():
    data = request.get_json()

    # Validate if 'type' and 'name' are present
    entry_type = data.get("type")
    name = data.get("name")

    if not isinstance(name, str) or not name.strip():
        return jsonify({"error": "Invalid or missing name"}), 400

    if entry_type not in ["recipe", "ingredient"]:
        return jsonify({"error": "Invalid entry type"}), 400

    # Ensure unique name
    if name in cookbook:
        return jsonify({"error": "Entry name must be unique"}), 400

    if entry_type == "ingredient":
        # Validate cookTime
        cook_time = data.get("cookTime")
        if not isinstance(cook_time, int) or cook_time < 0:
            return jsonify({"error": "cookTime must be an integer ≥ 0"}), 400
        
        # Create and store ingredient
        cookbook[name] = Ingredient(name=name, cook_time=cook_time)

    elif entry_type == "recipe":
        # Validate requiredItems
        required_items = data.get("requiredItems")
        if not isinstance(required_items, list):
            return jsonify({"error": "requiredItems must be a list"}), 400
        
        # Ensure no duplicate names in requiredItems
        duplicate_names = set()
        formatted = []
        for item in required_items:
            item_name = item.get("name")
            quantity = item.get("quantity")

            if not isinstance(item_name, str) or not item_name.strip():
                return jsonify({"error": "Invalid requiredItem name"}), 400
            if not isinstance(quantity, int) or quantity <= 0:
                return jsonify({"error": "Invalid quantity in requiredItems"}), 400
            if item_name in duplicate_names:
                return jsonify({"error": "Duplicate requiredItem names not allowed"}), 400

            duplicate_names.add(item_name)
            formatted.append(RequiredItem(name=item_name, quantity=quantity))

        # Create and store recipe
        cookbook[name] = Recipe(name=name, required_items=formatted)

    return jsonify({}), 200

# [TASK 3] ====================================================================
# Endpoint that returns a summary of a recipe that corresponds to a query name
@app.route('/summary', methods=['GET'])
def summary():
    recipe_name = request.args.get("name")

    if not recipe_name or recipe_name not in cookbook:
        return jsonify({"error": "Recipe not found"}), 400

    recipe = cookbook[recipe_name]
    if not isinstance(recipe, Recipe):
        return jsonify({"error": "Requested item is not a recipe"}), 400

    # use a helper function to calculate the recipe ingredients, doiung necessary recursions
    try:
        total_cook_time, ingredient_list = get_recipe_details(recipe)
    except KeyError:
        return jsonify({"error": "Recipe contains unknown ingredients"}), 400

    # Return the recipe summary as json
    return jsonify({
        "name": recipe_name,
        "cookTime": total_cook_time,
        "ingredients": ingredient_list
    }), 200


def get_recipe_details(recipe: Recipe):

    total_cook_time = 0
    ingredient_count = {}

    def process_required_item(item_name, quantity):
        nonlocal total_cook_time

        if item_name not in cookbook:
            raise KeyError  # Triggers HTTP 400 for unknown ingredients

        item = cookbook[item_name]

        if isinstance(item, Ingredient):
            # Base case: If it's an ingredient, add its cookTime
            total_cook_time += item.cook_time * quantity
            ingredient_count[item_name] = ingredient_count.get(item_name, 0) + quantity

        elif isinstance(item, Recipe):
            # Recursive case: If it's a recipe, process its requiredItems
            for req in item.required_items:
                process_required_item(req.name, req.quantity * quantity)

    for req in recipe.required_items:
        process_required_item(req.name, req.quantity)

    ingredient_list = [{"name": name, "quantity": qty} for name, qty in ingredient_count.items()]

    return total_cook_time, ingredient_list



# =============================================================================
# ==== DO NOT TOUCH ===========================================================
# =============================================================================

if __name__ == '__main__':
	app.run(debug=True, port=8080)
