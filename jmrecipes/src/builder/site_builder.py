from collections import defaultdict
import math
from src.utils import units
from src.utils import utils
from src.utils.utils import ingredients_in, scales_in, multiply_nutrition


def set_child_recipe_links(site):
    """Sets link data for parent ingredients.

    Sets the following keys for parent ingredients:
    - 'recipe_url' (str)
    """

    for ingredient in ingredients_in(site):
        if ingredient["is_recipe"]:
            ingredient["recipe_url"] = "../" + ingredient["recipe_slug"]

    return site


def set_recipes_used_in(site):
    """Sets link data for child recipes.

    Sets the following keys for each recipe:
    - 'used_in_any' (bool)

    Sets the following keys for each child recipe:
    - 'used_in' (list)
    """

    for recipe in site["recipes"]:
        recipe["used_in_any"] = False

    for parent_recipe, ingredient in ingredients_in(site, include="r"):
        if ingredient["is_recipe"]:
            child_recipe = recipe_from_slug(ingredient["recipe_slug"], site["recipes"])
            child_recipe["used_in_any"] = True
            child_recipe = add_used_in(child_recipe, parent_recipe)

    # remove duplicates
    for recipe in site["recipes"]:
        if recipe["used_in_any"]:
            recipe["used_in"] = [
                dict(t) for t in {tuple(d.items()) for d in recipe["used_in"]}
            ]

    return site


def recipe_from_slug(slug, recipes):
    """Returns recipe dictionary that matches slug."""

    for recipe in recipes:
        if recipe["url_slug"] == slug:
            return recipe

    raise ValueError(f"Could not find recipe with slug: {slug}")


def add_used_in(child_recipe, parent_recipe):
    """Add parent recipe data to child recipe."""

    if "used_in" not in child_recipe:
        child_recipe["used_in"] = []

    child_recipe["used_in"].append(
        {"title": parent_recipe["title"], "slug": parent_recipe["url_slug"]}
    )
    return child_recipe


def set_ingredient_as_recipe_quantities(site):
    """Sets recipe quantities for each parent ingredient.

    Sets the following keys for each parent ingredient:
    - 'recipe_quantity' (float)
    """

    for ingredient in ingredients_in(site):
        if ingredient["is_recipe"]:
            set_recipe_quantity(ingredient, site["recipes"])
    return site


def set_recipe_quantity(ingredient, recipes) -> None:
    """Sets recipe quantity for a parent ingredient."""

    number = ingredient["number"]
    unit = ingredient["unit"]
    recipe = recipe_from_slug(ingredient["recipe_slug"], recipes)
    ingredient["recipe_quantity"] = recipe_quantity(number, unit, recipe)


def recipe_quantity(amount, unit, recipe) -> float:
    """Returns the number of recipes produce an amount and unit.

    Returns 0 if no compatible yields.
    """

    for yielb in recipe["yield"]:
        yield_unit = yielb["unit"]
        if (
            units.is_volume(unit)
            and units.is_volume(yield_unit)
            or units.is_weight(unit)
            and units.is_weight(yield_unit)
        ):
            return (
                amount
                * units.to_standard(unit)
                / units.to_standard(yield_unit)
                / yielb["number"]
            )
        elif units.is_equivalent(unit, yield_unit):
            return amount / yielb["number"]
    return 0


def set_costs(site):
    """Set costs for each ingredients and recipe scale.

    Sets the following keys for each scale:
    - 'cost' (float)
    - 'cost_final' (bool)

    Sets the following keys for each ingredient:
    - 'cost' (float)
    - 'cost_final' (bool)
    """

    for ingredient in ingredients_in(site):
        ingredient["cost_final"] = False

    for scale in scales_in(site):
        scale["cost_final"] = False

    for ingredient in ingredients_in(site, keys="explicit_cost"):
        ingredient["cost"] = ingredient["explicit_cost"]
        ingredient["cost_final"] = True

    for ingredient in ingredients_in(
        site, values={"is_grocery": True, "cost_final": False}
    ):
        if not ingredient["has_matching_grocery"]:
            ingredient["cost"] = 0
        else:
            ingredient["cost"] = (
                ingredient["grocery_count"] * ingredient["grocery"]["cost"]
            )
        ingredient["cost_final"] = True

    for recipe, scale in scales_in(site, include="r"):
        if "explicit_cost" in recipe:
            scale["cost"] = recipe["explicit_cost"] * scale["multiplier"]
            scale["cost_final"] = True

    while recipes_cost_pending_count(site):
        calculate_ingredient_costs(site)
        pre_pending_count = recipes_cost_pending_count(site)
        calculate_recipe_costs(site)
        post_pending_count = recipes_cost_pending_count(site)
        if pre_pending_count == post_pending_count:
            raise ValueError("Cyclic recipe reference found")

    return site


def recipes_cost_pending_count(site) -> int:
    """Number of recipe scales where cost_final is False."""

    count = 0
    for scale in scales_in(site):
        if not scale["cost_final"]:
            count += 1
    return count


def calculate_ingredient_costs(site) -> None:
    """Tries to calculate costs of parent ingredients.

    Sets ingredient cost if child recipe's cost is final.
    """

    for ingredient in ingredients_in(site):
        if ingredient["is_recipe"]:
            child_recipe = recipe_from_slug(ingredient["recipe_slug"], site["recipes"])
            if child_recipe["scales"][0]["cost_final"]:
                ingredient["recipe_cost"] = child_recipe["scales"][0]["cost"]
                ingredient["cost"] = (
                    ingredient["recipe_quantity"] * ingredient["recipe_cost"]
                )
                ingredient["cost_final"] = True


def calculate_recipe_costs(site) -> None:
    """Tries to calculate costs of recipes.

    Sets recipe cost if all ingredients' costs are final.
    """

    for scale in scales_in(site):
        if not scale["cost_final"] and ingredients_costs_final(scale):
            scale["cost"] = sum_ingredient_cost(scale)
            scale["cost_final"] = True


def ingredients_costs_final(scale):
    """True if all ingredients' costs are final."""

    for ingredient in scale["ingredients"]:
        if not ingredient["cost_final"]:
            return False
    return True


def sum_ingredient_cost(scale) -> float:
    """Returns the cost of a scale by adding each ingredient."""

    cost = 0
    for ingredient in scale["ingredients"]:
        cost += ingredient["cost"]
    return cost


def set_costs_per_serving(site):
    """Sets cost per serving for each ingredient and recipe scale.

    Sets the following keys for each scale:
    - 'cost_per_serving' (float)

    Sets the following keys for each ingredient:
    - 'cost_per_serving' (float)
    """

    for scale in scales_in(site):
        servings = scale["servings"] if scale["has_servings"] else 1
        scale["cost_per_serving"] = scale["cost"] / servings

    for scale, ingredient in ingredients_in(site, include="s"):
        servings = scale["servings"] if scale["has_servings"] else 1
        ingredient["cost_per_serving"] = ingredient["cost"] / servings

    return site


def set_cost_strings(site):
    """Sets formatted cost strings for ingredients and scales.

    Sets the following keys for each ingredient:
    - 'cost_string' (str)
    - 'cost_per_serving_string' (str)

    Sets the following keys for each scale:
    - 'cost_string' (str)
    - 'cost_per_serving_string' (str)
    - 'has_visible_cost' (bool)
    - 'has_visible_cost_per_serving' (bool)
    """

    for ingredient in ingredients_in(site):
        ingredient["cost_string"] = utils.format_currency(ingredient["cost"])
        ingredient["cost_per_serving_string"] = utils.format_currency(
            ingredient["cost_per_serving"]
        )

    for recipe, scale in scales_in(site, include="r"):
        scale["cost_string"] = utils.format_currency(scale["cost"])
        scale["cost_per_serving_string"] = utils.format_currency(
            scale["cost_per_serving"]
        )
        scale["has_visible_cost"] = not recipe["hide_cost"] and bool(scale["cost"] > 0)
        scale["has_visible_cost_per_serving"] = (
            scale["has_visible_cost"]
            and scale["has_servings"]
            and scale["servings"] != 1
        )
    return site


def set_nutrition(site):
    """Set nutrition for each ingredients and recipe scale.

    Sets the following keys for each scale:
    - 'nutrition' (dict)
    - 'nutrition_final' (bool)

    Sets the following keys for each ingredient:
    - 'nutrition' (dict)
    - 'nutrition_final' (bool)
    - 'has_nutrition' (bool)
    """

    for ingredient in ingredients_in(site):
        ingredient["nutrition_final"] = False

    for scale in scales_in(site):
        scale["nutrition_final"] = False

    for ingredient in ingredients_in(site, keys="explicit_nutrition"):
        ingredient["nutrition"] = ingredient["explicit_nutrition"]
        ingredient["has_nutrition"] = True
        ingredient["nutrition_final"] = True

    for recipe, scale, ingredient in ingredients_in(
        site, values={"is_grocery": True, "nutrition_final": False}, include="rs"
    ):
        if not ingredient["has_matching_grocery"]:
            ingredient["nutrition"] = empty_nutrition()
            ingredient["has_nutrition"] = False
        else:
            ingredient["nutrition"] = multiply_nutrition(
                ingredient["grocery"]["nutrition"], ingredient["grocery_count"]
            )
            ingredient["has_nutrition"] = True
        ingredient["nutrition_final"] = True

    for recipe, scale in scales_in(site, include="r"):
        if "explicit_nutrition" in recipe:
            scale["nutrition"] = multiply_nutrition(
                recipe["explicit_nutrition"], scale["multiplier"]
            )
            scale["nutrition_final"] = True

    while recipes_nutrition_pending_count(site):
        calculate_ingredient_nutrition(site)
        pre_pending_count = recipes_nutrition_pending_count(site)
        calculate_recipes_nutrition(site)
        post_pending_count = recipes_nutrition_pending_count(site)
        if pre_pending_count == post_pending_count:
            raise ValueError("Cyclic recipe reference found")

    return site


# todo has_nutrition to flags


def recipes_nutrition_pending_count(site) -> int:
    """Number of recipe scales where nutrition_final is False."""

    count = 0
    for scale in scales_in(site):
        if not scale["nutrition_final"]:
            count += 1
    return count


def calculate_ingredient_nutrition(site) -> None:
    """Tries to calculate nutrition of parent ingredients.

    Sets ingredient nutrition if child recipe's nutrition is final.
    """

    for ingredient in ingredients_in(site):
        if ingredient["is_recipe"]:
            child_recipe = recipe_from_slug(ingredient["recipe_slug"], site["recipes"])
            if child_recipe["scales"][0]["nutrition_final"]:
                ingredient["recipe_nutrition"] = child_recipe["scales"][0]["nutrition"]
                ingredient["nutrition"] = multiply_nutrition(
                    ingredient["recipe_nutrition"], ingredient["recipe_quantity"]
                )
                ingredient["has_nutrition"] = True
                ingredient["nutrition_final"] = True


def calculate_recipes_nutrition(site):
    """Tries to calculate nutrition of recipes.

    Sets recipe nutrition if all ingredients' nutritions are final.
    """

    for scale in scales_in(site):
        if not scale["nutrition_final"] and ingredients_nutrition_final(scale):
            scale["nutrition"] = sum_ingredient_nutrition(scale)
            scale["nutrition_final"] = True


def ingredients_nutrition_final(scale):
    """True if all ingredients' nutritions are final."""

    for ingredient in scale["ingredients"]:
        if not ingredient["nutrition_final"]:
            return False
    return True


def sum_ingredient_nutrition(scale) -> dict:
    """Returns the nutrition of a scale by adding each ingredient."""

    nutrition = empty_nutrition()
    for ingredient in scale["ingredients"]:
        nutrition["calories"] += ingredient["nutrition"]["calories"]
        nutrition["fat"] += ingredient["nutrition"]["fat"]
        nutrition["protein"] += ingredient["nutrition"]["protein"]
        nutrition["carbohydrates"] += ingredient["nutrition"]["carbohydrates"]
    return nutrition


def empty_nutrition() -> dict:
    """Returns a nutrition with zero values."""

    return {"calories": 0, "fat": 0, "carbohydrates": 0, "protein": 0}


def set_display_nutrition(site):
    """Sets nutrition to display for each scale and each ingredient.

    If servings are set, nutrition to display is nutrition per serving,
    otherwise, it is the total nutrition.

    Sets the following keys for each scale:
    - 'nutrition_display' (dict)
    - 'has_visible_nutrition' (bool)
    - 'is_nutrition_per_serving' (bool)

    Sets the following keys for each ingredient:
    - 'nutrition_display' (dict)
    """

    for scale, ingredient in ingredients_in(site, include="s"):
        servings = scale.get("servings", 1)
        ingredient["nutrition_display"] = multiply_nutrition(
            ingredient["nutrition"], 1 / servings, round_result=True
        )

    for recipe, scale in scales_in(site, include="r"):
        servings = scale.get("servings", 1)
        scale["nutrition_display"] = multiply_nutrition(
            scale["nutrition"], 1 / servings, round_result=True
        )
        scale["has_visible_nutrition"] = scale_has_visible_nutrition(scale, recipe)
        scale["is_nutrition_per_serving"] = servings != 1

    return site


def scale_has_visible_nutrition(scale, recipe) -> bool:
    """Determines if a scale's nutrition should be visible."""

    if recipe["hide_nutrition"]:
        return False
    if "explicit_nutrition" in recipe:
        return True
    return has_nutrients(scale["nutrition"])


def has_nutrients(nutrition: dict):
    """Return True if any item in nutrition is nonzero."""

    for value in nutrition.values():
        if value > 0:
            return True
    return False


def set_ingredient_details(site):
    """Sets ingredient detail info.

    Sets the following keys for each recipe:
    - 'has_cost_detail' (bool)
    - 'has_cost_per_serving_detail' (bool)
    - 'has_nutrition_detail' (bool)

    Sets the following keys for each scale:
    - 'has_cost_detail' (bool)
    - 'has_cost_per_serving_detail' (bool)
    - 'has_nutrition_detail' (bool)
    - 'has_any_detail' (bool)
    """

    for recipe, scale in scales_in(site, include="r"):
        explicit_cost = "explicit_cost" in recipe
        explicit_nutrition = "explicit_nutrition" in recipe
        cost_hidden = recipe["hide_cost"]
        scale["has_cost_detail"] = (
            has_cost_detail(scale) and not cost_hidden and not explicit_cost
        )
        scale["has_cost_per_serving_detail"] = (
            scale["has_cost_detail"] and scale["has_servings"]
        )
        scale["has_nutrition_detail"] = (
            scale["has_visible_nutrition"] and not explicit_nutrition
        )
        scale["has_any_detail"] = (
            scale["has_cost_detail"]
            or scale["has_cost_per_serving_detail"]
            or scale["has_nutrition_detail"]
        )

    for recipe in site["recipes"]:
        recipe["has_cost_detail"] = False
        recipe["has_cost_per_serving_detail"] = False
        recipe["has_nutrition_detail"] = False
        for scale in recipe["scales"]:
            if scale["has_cost_detail"]:
                recipe["has_cost_detail"] = True
            if scale["has_cost_per_serving_detail"]:
                recipe["has_cost_per_serving_detail"] = True
            if scale["has_nutrition_detail"]:
                recipe["has_nutrition_detail"] = True

    return site


def has_cost_detail(scale) -> bool:
    """True if any ingredient has nonzero cost."""

    for ingredient in scale["ingredients"]:
        if ingredient["cost"]:
            return True
    return False


def has_nutrition_detail(scale) -> bool:
    """True if any ingredient has nutrition detail."""

    for ingredient in scale["ingredients"]:
        if ingredient["has_nutrition"]:
            return True
    return False


def set_description_areas(site):
    """Sets recipe data regarding the description area.

    Sets the following keys for each scale:
    - 'has_description_area' (bool)
    """

    for recipe, scale in scales_in(site, include="r"):
        scale["has_description_area"] = (
            scale["has_visible_yields"]
            or scale["has_visible_serving_sizes"]
            or scale["has_times"]
            or scale["has_visible_cost"]
            or recipe["has_description"]
            or recipe["used_in_any"]
            or recipe["has_linked_videos"]
        )
    return site


def set_ingredient_lists(site):
    """Groups ingredients into ingredient lists.

    Sets the following keys for each scale:
    - 'ingredient_lists' (dict)
    """

    for scale in scales_in(site):
        scale["ingredient_lists"] = defaultdict(list)
        for ingredient in scale["ingredients"]:
            scale["ingredient_lists"][ingredient.get("list", "Ingredients")].append(
                ingredient
            )
    return site


def link_recipes_collections(site):
    """Adds collections data to recipes and vice versa.

    Sets the following keys for each recipe:
    - 'collections' (list)

    Sets the following keys for each collection:
    - 'recipes' (list)
    """

    for recipe in site["recipes"]:
        recipe["collections"] = []

    for collection in site["collections"]:
        for i, url_slug in enumerate(collection["recipes"]):
            for recipe in site["recipes"]:
                if recipe["url_slug"] == url_slug:
                    recipe["collections"].append(info_for_recipe(collection))
                    collection["recipes"][i] = info_for_collection(recipe)

    return site


def info_for_collection(recipe) -> dict:
    """Recipe data needed for collection page."""

    keys = (
        "title",
        "url_slug",
        "subtitle",
        "has_subtitle",
        "image_url",
        "search_targets",
    )
    return {k: recipe[k] for k in keys if k in recipe}


def info_for_recipe(collection) -> dict:
    """Collection data needed for recipe page."""

    keys = ("name", "url_path", "label", "href")
    return {k: collection[k] for k in keys if k in collection}


def set_search_values(site):
    """Adds data needed for search function.

    Sets the following keys for each collection:
    - 'search_group_interval' (int)

    Sets the following keys for each recipe in collection:
    - 'index' (int)
    """

    for collection in site["collections"]:
        for i, recipe in enumerate(collection["recipes"], 1):
            recipe["index"] = i
        collection["search_group_interval"] = 10 ** math.ceil(math.log10(i))

    return site


def set_summary(site):
    """Adds summary data to site.

    Sets the following keys for the site:
    - 'summary' (dict)
    """

    site["summary"] = {
        "recipes": summary_recipes(site),
        "collections": summary_collections(site),
        "ingredients": summary_ingredients(site),
    }
    return site


def summary_recipes(site):
    """Summary data for recipes."""

    recipes = []
    for recipe in site["recipes"]:
        recipes.append(
            {
                "title": recipe["title"],
                "collections": [c["name"] for c in recipe["collections"]],
            }
        )
    return recipes


def summary_collections(site):
    """Summary data for collections."""

    collections = []
    for collection in site["collections"]:
        collections.append(
            {
                "name": collection["name"],
                "recipes": [r["title"] for r in collection["recipes"]],
            }
        )
    return collections


def summary_ingredients(site: dict) -> list[dict]:
    """Summary data for ingredients."""

    ingredients = []
    for recipe, scale, ingredient in ingredients_in(site, include="rs"):
        ingredients.append(
            {
                "recipe": recipe["title"],
                "scale": scale["label"],
                "ingredient": ingredient["string"],
                "found_grocery": ingredient["has_matching_grocery"],
                "number_groceries": round(ingredient.get("grocery_count", 0), 5),
            }
        )
    return ingredients
