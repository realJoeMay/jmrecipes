from urllib.parse import urlparse
from collections import defaultdict
import json

from src.utils import utils
from src.utils import units
from src.utils.utils import ingredients_in, scales_in, multiply_nutrition


def set_defaults(recipe):
    """Sets default values for keys if not already set.

    Sets the following default values:
    - 'hide_cost': (from config)
    - 'hide_nutrition': (from config)

    Sets the following default values for each yield:
    - 'unit': 'servings'
    - 'show_yield': True
    - 'show_serving_size': False

    Sets the following default values for each video:
    - 'list': (from config)

    Sets the following default values for each instruction step:
    - 'list': Instructions
    """

    for yielb in recipe["yield"]:
        if "unit" not in yielb:
            yielb["unit"] = "servings"
        if "show_yield" not in yielb:
            yielb["show_yield"] = True
        if "show_serving_size" not in yielb:
            yielb["show_serving_size"] = False

    for step in recipe["instructions"]:
        if "list" not in step:
            step["list"] = "Instructions"

    if "hide_cost" not in recipe:
        recipe["hide_cost"] = utils.config("default", "hide_cost", as_boolean=True)
    if "hide_nutrition" not in recipe:
        recipe["hide_nutrition"] = utils.config(
            "default", "hide_nutrition", as_boolean=True
        )

    return recipe


def set_url(recipe):
    """Sets values regarding the URLs for the given recipe.

    Sets the following keys:
    - 'url_path' (str)
    - 'url' (str)
    - 'feedback_url' (str)
    """

    recipe["url_path"] = "/" + recipe["url_slug"]
    recipe["url"] = utils.make_url(path=recipe["url_path"])
    recipe["feedback_url"] = utils.feedback_url(recipe["title"], recipe["url"])
    return recipe


def set_subtitle(recipe):
    """Sets values related to the recipe's subtitle.

    Sets the following keys:
    - 'has_subtitle' (bool)
    """

    if "subtitle" in recipe and recipe["subtitle"] != "":
        recipe["has_subtitle"] = True
        recipe["subtitle"] = recipe["subtitle"].lower()
    else:
        recipe["has_subtitle"] = False

    return recipe


def set_description(recipe):
    """Sets a flag indicating the presence of a recipe description.

    Sets the following keys:
    - 'has_description' (bool)
    """

    recipe["has_description"] = "description" in recipe
    return recipe


def set_image(recipe):
    """Sets the image URL for the recipe.

    Sets the following keys:
    - 'has_image' (bool)
    - 'image_url' (str)
    """

    if recipe["has_image"]:
        recipe["image_url"] = "/".join((recipe["url_slug"], recipe["image"]))
    else:
        recipe["image_url"] = "default.jpg"
    return recipe


def set_scales(recipe):
    """Sets scale-related values for each scale.

    Sets the following keys:
    - 'base_select_class' (str)
    - 'has_scales' (bool)

    Sets the following keys for each scale:
    - 'label' (str)
    - 'item_class' (str)
    - 'select_class' (str)
    - 'button_class' (str)
    - 'js_function_name' (str)
    - 'keyboard_shortcut' (str)
    """

    for i, scale in enumerate(recipe["scales"], 1):
        label = str(scale["multiplier"].limit_denominator(100)).replace("/", "_") + "x"
        scale["label"] = label
        scale["item_class"] = f"scale-{label}"
        scale["select_class"] = f"display-scale-{label}"
        scale["button_class"] = f"display-scale-{label}-btn"
        scale["js_function_name"] = f"scale{label}"
        scale["keyboard_shortcut"] = i
    recipe["base_select_class"] = recipe["scales"][0]["select_class"]
    recipe["has_scales"] = len(recipe["scales"]) > 1
    return recipe


def set_times(recipe):
    """Set recipe attributes related to cook times.

    Sets the following keys for each scale:
    - 'times' (list)
    - 'has_times' (bool)

    Sets the following keys for each time:
    - 'unit' (str)
    - 'time_string' (str)
    """

    for time in recipe["times"]:

        if "unit" not in time or time["unit"] == "":
            time["unit"] = "minutes" if time["time"] > 1 else "minute"

        time_string = utils.fraction_to_string(time["time"])
        time["time_string"] = f'{time_string} {time["unit"]}'

    for scale in recipe["scales"]:
        scale["times"] = recipe["times"]
        scale["has_times"] = bool(scale["times"])

    return recipe


def scale_yields(recipe):
    """Add yield section to each scale.

    Sets the following keys for each scale:
    - 'yield' (list)
    """

    for scale in recipe["scales"]:
        scale["yield"] = []
        for yielb in recipe["yield"]:
            number = yielb["number"] * scale["multiplier"]
            scale["yield"].append(
                {
                    "number": number,
                    "unit": units.numberize(yielb["unit"], number),
                    "show_yield": yielb["show_yield"],
                    "show_serving_size": yielb["show_serving_size"],
                }
            )
    return recipe


def set_servings(recipe):
    """Sets servings data for each scale.

    Sets the following keys:
    - 'has_servings' (bool)

    Sets the following keys for each scale:
    - 'has_servings' (bool)

    Sets the following keys for each scale with servings:
    - 'servings' (int)
    """

    for scale in recipe["scales"]:
        scale["has_servings"] = False
        for yielb in scale["yield"]:
            if yielb["unit"].lower() in ("serving", "servings"):
                scale["servings"] = yielb["number"]
                scale["has_servings"] = True

    recipe["has_servings"] = recipe["scales"][0]["has_servings"]
    return recipe


def set_visible_yields(recipe):
    """Sets yield data to appear on page.

    Sets the following keys for each scale:
    - 'has_visible_yields' (bool)

    Sets the following keys for each yield:
    - 'yield_string' (str)
    """

    for scale in recipe["scales"]:
        scale["has_visible_yields"] = False
        for yielb in scale["yield"]:
            if yielb["show_yield"]:
                scale["has_visible_yields"] = True
                yielb["yield_string"] = yield_string(yielb)

    return recipe


def yield_string(yielb: dict) -> str:
    """String represeentation of a yield."""

    number = utils.fraction_to_string(yielb["number"])
    return f'{number} {yielb["unit"]}'


def set_visible_serving_sizes(recipe):
    """Sets servings size data for each scale.

    Sets the following keys for each scale:
    - 'has_visible_serving_sizes' (bool)

    Sets the following keys for each yield if showing serving size:
    - 'serving_size_string' (str)
    """

    for scale in recipe["scales"]:
        scale = set_serving_size(scale)
    return recipe


def set_serving_size(scale):
    """Sets servings size data for a scale."""

    scale["has_visible_serving_sizes"] = False

    if scale["has_servings"] is False:
        return scale

    for yielb in scale["yield"]:
        if yielb["show_serving_size"]:
            scale["has_visible_serving_sizes"] = True
            number = yielb["number"] / scale["servings"]
            number_string = utils.fraction_to_string(number)
            unit = units.numberize(yielb["unit"], number)
            yielb["serving_size_string"] = f"{number_string} {unit}"
    return scale


def set_copy_ingredients_sublabel(recipe):
    """Set sublabel of copy ingredients button for each scale.

    Sets the following keys for each scale:
    - 'copy_ingredients_sublabel' (str)
    """

    for scale in recipe["scales"]:
        scale["copy_ingredients_sublabel"] = copy_ingredients_sublabel(scale)
    return recipe


def copy_ingredients_sublabel(scale: dict) -> str:
    """Returns sublabel for copy ingredients button.

    The sublabel is based on the following:
    - [Empty string] if scale is base scale
    - '4 servings' if servings is set
    - '2x' otherwise
    """

    if scale["multiplier"] == 1:
        return ""

    if scale["has_servings"]:
        unit = "serving" if scale["servings"] == 1 else "servings"
        return f'for {scale["servings"]} {unit}'

    return f'for {scale["multiplier"]}x'


def set_ingredients_type(recipe):
    """Sets the ingredient type for each ingredient.

    Sets the following keys for each ingredient:
    - 'is_recipe' (bool)
    - 'is_grocery' (bool)
    """

    for ingredient in recipe["ingredients"]:
        ingredient["is_recipe"] = "recipe_slug" in ingredient
        ingredient["is_grocery"] = not (ingredient["is_recipe"])
    return recipe


def scale_ingredients(recipe):
    """Add ingredients list to each recipe scale.

    Sets the following keys for each scale:
    - 'ingredients' (list)
    - 'has_ingredients' (bool)
    """

    for scale in recipe["scales"]:
        scale["ingredients"] = ingredients_in_scale(
            recipe["ingredients"], scale["multiplier"]
        )
        scale["has_ingredients"] = bool(scale["ingredients"])
    return recipe


def ingredients_in_scale(base_ingredients, multiplier) -> list:
    """Get list of ingredients for a recipe scale.

    Ingredients are scaled using a multiplier. If the base
    ingredient has an explicit scale, the ingredient is copied without
    multiplying.
    """

    ingredients = []
    for ingredient in base_ingredients:
        if "scale" not in ingredient:
            ingredients.append(multiply_ingredient(ingredient, multiplier))
        elif utils.to_fraction(ingredient["scale"]) == multiplier:
            ingredients.append(ingredient)
    return ingredients


def multiply_ingredient(ingredient, multiplier) -> dict:
    """Returns ingredient data scaled by multiplier."""

    scaled = ingredient.copy()
    scaled["number"] = ingredient["number"] * multiplier
    scaled["display_number"] = ingredient["display_number"] * multiplier
    if "explicit_cost" in ingredient:
        scaled["explicit_cost"] = ingredient["explicit_cost"] * multiplier
    if "explicit_nutrition" in ingredient:
        scaled["explicit_nutrition"] = multiply_nutrition(
            ingredient["explicit_nutrition"], multiplier
        )
    return scaled


def set_ingredient_outputs(recipe):
    """Sets display values for ingredients.

    Sets the following keys for each scaled ingredient:
    - 'string' (str)
    - 'display_amount' (str)
    """

    for ingredient in ingredients_in(recipe):
        if ingredient["display_number"] == 0:
            ingredient["display_number"] = ingredient["number"]
        if ingredient["display_unit"] == "":
            ingredient["display_unit"] = ingredient["unit"]
        if ingredient["display_item"] == "":
            ingredient["display_item"] = ingredient["item"]
        ingredient["string"] = ingredient_string(ingredient)
        ingredient["display_amount"] = ingredient_display_amount(ingredient)
    return recipe


def ingredient_string(ing: dict) -> str:
    """String for ingredient with number, unit, and item."""

    i_str = []
    if ing["display_number"]:
        i_str.append(utils.fraction_to_string(ing["display_number"]))
    if ing["display_unit"]:
        i_str.append((ing["display_unit"]))
    if ing["display_item"]:
        i_str.append((ing["display_item"]))
    string = " ".join(i_str)
    return string


def ingredient_display_amount(ingredient):
    """String for ingredient with number and unit."""

    amount = []
    if ingredient["display_number"]:
        amount.append(utils.fraction_to_string(ingredient["display_number"]))
    if ingredient["display_unit"]:
        amount.append((ingredient["display_unit"]))
    return " ".join(amount)


def lookup_groceries(recipe):
    """Looks up grocery info for each ingredient.

    Sets the following keys for each scaled ingredient:
    - 'grocery' (dict)
    - 'has_matching_grocery' (bool)
    - 'grocery_count' (float)
    """

    for ingredient in ingredients_in(recipe):
        lookup_grocery(ingredient)
        ingredient["grocery_count"] = grocery_count(ingredient)
    return recipe


def lookup_grocery(ingredient):
    """Adds grocery data to ingredient."""

    ingredient["has_matching_grocery"] = False
    grocery = utils.grocery_info(ingredient["item"])

    if grocery is None:
        return

    ingredient["has_matching_grocery"] = True
    grocery_keys = [
        "name",
        "cost",
        "volume_amount",
        "volume_unit",
        "weight_amount",
        "weight_unit",
        "other_amount",
        "other_unit",
        "discrete_amount",
        "calories",
        "fat",
        "carbohydrates",
        "protein",
        "tags",
    ]
    ingredient["grocery"] = {k: grocery[k] for k in grocery_keys}
    ingredient["grocery"]["nutrition"] = {
        "calories": ingredient["grocery"].pop("calories"),
        "fat": ingredient["grocery"].pop("fat"),
        "carbohydrates": ingredient["grocery"].pop("carbohydrates"),
        "protein": ingredient["grocery"].pop("protein"),
    }
    ingredient["grocery"]["tags"] = ingredient["grocery"]["tags"].split("\n")


def grocery_count(ingredient) -> float:
    """Returns how many grocery items are in the ingredient."""

    if not ingredient["has_matching_grocery"]:
        return 0

    ingredient_unit = ingredient["unit"]

    if ingredient_unit == "":
        func = grocery_number_discrete
    elif units.is_volume(ingredient_unit):
        func = grocery_number_volume
    elif units.is_weight(ingredient_unit):
        func = grocery_number_weight
    else:
        func = grocery_number_other

    return func(ingredient)


def grocery_number_discrete(ingredient):
    """Number of groceries in ingredient, measured by count."""

    grocery_count = ingredient["grocery"]["discrete_amount"]
    if grocery_count == 0:
        return 0

    return ingredient["number"] / grocery_count


def grocery_number_volume(ingredient):
    """Number of groceries in ingredient, measured by volume."""

    ingredient_number = ingredient["number"]
    ingredient_unit = ingredient["unit"]
    grocery_number = ingredient["grocery"]["volume_amount"]
    grocery_unit = ingredient["grocery"]["volume_unit"]

    if grocery_number == 0:
        return 0
    if grocery_unit == "":
        return 0
    if not units.is_volume(grocery_unit):
        return 0

    ingredient_unit_to_standard = units.to_standard(ingredient_unit)
    grocery_unit_to_standard = units.to_standard(grocery_unit)
    return (
        ingredient_number
        * ingredient_unit_to_standard
        / grocery_number
        / grocery_unit_to_standard
    )


def grocery_number_weight(ingredient):
    """Number of groceries in ingredient, measured by weight."""

    ingredient_number = ingredient["number"]
    ingredient_unit = ingredient["unit"]
    grocery_number = ingredient["grocery"]["weight_amount"]
    grocery_unit = ingredient["grocery"]["weight_unit"]

    if grocery_number == 0:
        return 0
    if grocery_unit == "":
        return 0
    if not units.is_weight(grocery_unit):
        return 0

    ingredient_unit_to_standard = units.to_standard(ingredient_unit)
    grocery_unit_to_standard = units.to_standard(grocery_unit)
    return (
        ingredient_number
        * ingredient_unit_to_standard
        / grocery_number
        / grocery_unit_to_standard
    )


def grocery_number_other(ingredient):
    """Number of groceries in ingredient, measured by a nonstandard unit."""

    ingredient_number = ingredient["number"]
    ingredient_unit = ingredient["unit"]
    grocery_number = ingredient["grocery"]["other_amount"]
    grocery_unit = ingredient["grocery"]["other_unit"]

    if grocery_number == 0:
        return 0
    if grocery_unit == "":
        return 0
    if not units.is_equivalent(ingredient_unit, grocery_unit):
        return 0

    return ingredient_number / grocery_number


def set_instructions(recipe):
    """Sets instruction data for each scale.

    Sets the following keys for each scale:
    - 'instructions' (list)
    - 'has_instructions' (bool)
    """

    for scale in recipe["scales"]:
        scale["instructions"] = []
        for step in recipe["instructions"]:
            if (
                "scale" not in step
                or utils.to_fraction(step["scale"]) == scale["multiplier"]
            ):
                scale["instructions"].append(step.copy())

        scale["has_instructions"] = bool(scale["instructions"])

    recipe = set_instruction_lists(recipe)
    recipe = number_steps(recipe)
    return recipe


def set_instruction_lists(recipe):
    """Groups instruction steps into step lists."""

    for scale in recipe["scales"]:
        scale["instruction_lists"] = defaultdict(list)
        for step in scale["instructions"]:
            scale["instruction_lists"][step["list"]].append(step)
    return recipe


def number_steps(recipe):
    """Sets step numbers for instructions."""

    for scale in recipe["scales"]:
        for steps in scale["instruction_lists"].values():
            for i, step in enumerate(steps, 1):
                step["number"] = i
    return recipe


def set_sources(recipe):
    """Sets sources data.

    Sets the following keys:
    - 'has_sources' (bool)

    Sets the following keys for each source:
    - 'html' (str)
    """

    if "sources" not in recipe:
        recipe["has_sources"] = False
        return recipe

    for source in recipe["sources"]:
        source["html"] = source_html(source)

    recipe["has_sources"] = True

    return recipe


def source_html(source):
    """Returns link html for a source."""

    if "name" in source and "url" in source:
        return source_link(source["name"], source["url"])
    if "name" in source and "url" not in source:
        return source["name"]
    if "name" not in source and "url" in source:
        name = urlparse(source["url"]).netloc
        return source_link(name, source["url"])

    return ""


def source_link(name, url) -> str:
    """Returns html for link given name and url."""

    return f'<a href="{url}" target="_blank">{name}</a>'


def set_notes(recipe):
    """Set notes for each scale.

    Sets the following keys for each scale:
    - 'notes' (list)
    - 'has_notes' (bool)
    - 'has_notes_box' (bool)
    """

    for scale in recipe["scales"]:

        if "notes" in recipe:
            scale["notes"] = notes_for_scale(recipe["notes"], scale)
        else:
            scale["notes"] = []

        scale["has_notes"] = bool(scale["notes"])
        scale["has_notes_box"] = recipe["has_sources"] or scale["has_notes"]
    return recipe


def notes_for_scale(notes, scale) -> list:
    """Returns notes for a scale."""

    scale_notes = []
    for note in notes:
        if "scale" not in note or note["scale"] == scale["multiplier"]:
            scale_notes.append(note)
    return scale_notes


def set_videos(recipe):
    """Set videos for the recipe.

    Sets the following keys for the recipe:
    - 'embedded_videos' (list)
    - 'linked_videos' (list)
    - 'has_embedded_videos' (bool)
    - 'has_linked_videos' (bool)

    Sets the following keys for box_video:
    - 'url' (str)

    Sets the following keys for description_video:
    - 'url' (str)
    """

    recipe["embedded_videos"] = []
    recipe["linked_videos"] = []

    for video in recipe["videos"]:
        url = video["url"]
        if utils.is_youtube_url(url):
            video_id = utils.youtube_url_id(url)
            recipe["embedded_videos"].append(
                {"url": url, "embed_url": utils.youtube_embed_url(video_id)}
            )
        else:
            recipe["linked_videos"].append({"url": url})

    recipe["has_embedded_videos"] = bool(recipe["embedded_videos"])
    recipe["has_linked_videos"] = bool(recipe["linked_videos"])
    return recipe


def set_schema(recipe):
    """Add schema to recipe data.

    More on recipe schema: https://schema.org/Recipe

    Sets the following keys:
    - 'schema_str' (str)
    """

    schema = {
        "@context": "https://schema.org",
        "@type": "Recipe",
        "name": recipe["title"],
    }

    if recipe["has_image"]:
        schema["image"] = recipe["image"]

    if servings_schema(recipe):
        schema["recipeYield"] = servings_schema(recipe)

    if recipe["scales"][0]["has_ingredients"]:
        schema["recipeIngredient"] = []
        for ingredient in recipe["scales"][0]["ingredients"]:
            schema["recipeIngredient"].append(ingredient["string"])

    recipe["schema_string"] = json.dumps(schema)
    return recipe


def servings_schema(recipe) -> str:
    """Returns schema string for servings. Empty string if no servings."""

    if recipe["scales"][0]["has_servings"] is False:
        return ""

    number = recipe["scales"][0]["servings"]
    unit = "serving" if number == 1 else "servings"
    return f"{number} {unit}"


def set_search_targets(recipe):
    """Add search target data.

    Sets the following keys for each scale:
    - 'search_targets' (list)
    """

    recipe["search_targets"] = []
    recipe["search_targets"].append({"text": recipe["title"], "type": "title"})

    # subtitle
    if recipe["has_subtitle"]:
        recipe["search_targets"].append(
            {"text": recipe["subtitle"], "type": "subtitle"}
        )

    # ingredient
    for ingredient in recipe["scales"][0]["ingredients"]:
        recipe["search_targets"].append(
            {"text": ingredient["display_item"], "type": "ingredient"}
        )

    # ingredient tags
    for ingredient in recipe["scales"][0]["ingredients"]:
        if "grocery" in ingredient:
            for tag in ingredient["grocery"]["tags"]:
                recipe["search_targets"].append(
                    {
                        "text": f'{ingredient["display_item"]} ({tag})',
                        "type": "ingredient-tag",
                    }
                )

    for target in recipe["search_targets"]:
        target["class"] = "target-" + target["type"]

    return recipe
