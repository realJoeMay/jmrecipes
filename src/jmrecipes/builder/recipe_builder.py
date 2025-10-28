"""Recipe Builder Utilities"""

from collections import defaultdict
from fractions import Fraction
import json
from urllib.parse import urlparse

from jmrecipes.utils import utils
from jmrecipes.utils import units
from jmrecipes.utils import grocery
from jmrecipes.utils import parse
from jmrecipes.utils import nutrition
from jmrecipes.builder.iterate import ingredients_in


def standardize_yields(recipe):
    """Sets yield data from input file."""

    yield_data = recipe["file"].get("yield", [])
    if not isinstance(yield_data, (int, float, list)):
        raise TypeError("Yield data must be a number or a list.")

    recipe["yield"] = []
    if isinstance(yield_data, (int, float)):
        recipe["yield"].append(make_yield_item({"number": yield_data}))
    else:  # list
        for yield_item in yield_data:
            recipe["yield"].append(make_yield_item(yield_item))

    return recipe


def make_yield_item(data: dict) -> dict:
    """Formats yield data from input file."""

    if "number" not in data:
        raise KeyError("Yield data must have number field.")

    yielb = {}
    yielb["number"] = parse.to_fraction(data["number"])
    yielb["unit"] = data.get("unit", "servings")
    yielb["show_yield"] = bool(data.get("show_yield", True))
    yielb["show_serving_size"] = bool(data.get("show_serving_size", False))
    return yielb


def standardize_instructions(recipe):
    """Sets instructions data from input file."""

    recipe["instructions"] = []
    for step in recipe["file"].get("instructions", []):
        recipe["instructions"].append(make_step(step))

    return recipe


def make_step(data: str | dict) -> dict:
    """Formats instructions data from input file."""

    if not isinstance(data, (str, dict)):
        raise TypeError("Instructions step must be a string or dictionary.")
    if isinstance(data, dict) and "text" not in data:
        raise KeyError('Instructions step dict must include "text" field.')

    default_list = "Instructions"

    if isinstance(data, str):
        return {"text": data, "list": default_list}

    # data is dict with "text"
    step = {"text": data["text"], "list": data.get("list", default_list)}
    if "scale" in data:
        step["scale"] = data["scale"]
    if "list" in data:
        step["list"] = data["list"]
    return step


def standardize_ingredients(recipe):
    """Saves ingredient info from input file formats."""

    recipe["ingredients"] = []
    for ingredient in recipe["file"].get("ingredients", []):
        recipe["ingredients"].append(_read_ingredient(ingredient))
    return recipe


def _read_ingredient(data: dict | str) -> dict:
    """Formats ingredient data from input file."""

    # default values
    ingredient = {
        "number": 0,
        "unit": "",
        "item": "",
        "descriptor": "",
        "display_number": 0,
        "display_unit": "",
        "display_item": "",
    }

    if not isinstance(data, (str, dict)):
        raise TypeError("Ingredient must be a string or dictionary.")

    if isinstance(data, str):
        data_dict = {"text": data}
    else:  # dict
        data_dict = data

    if "text" in data_dict:
        ingredient.update(parse.ingredient(data_dict["text"]))

    # read number fields
    for field in ["number", "display_number"]:
        if field in data_dict:
            ingredient[field] = parse.to_fraction(data_dict[field])

    # read text fields
    for field in [
        "unit",
        "item",
        "descriptor",
        "display_unit",
        "display_item",
        "list",
        "scale",
    ]:
        if field in data_dict:
            ingredient[field] = data_dict[field]

    # read fields that change name
    if "cost" in data_dict:
        ingredient["explicit_cost"] = data_dict["cost"]
    if "nutrition" in data_dict:
        ingredient["explicit_nutrition"] = nutrition.read(data_dict["nutrition"])
    if "recipe" in data_dict:
        ingredient["recipe_slug"] = data_dict["recipe"]

    return ingredient


def set_title(recipe):
    """Sets values related to the recipe's title and subtitle.

    Sets the following keys:
    - 'has_subtitle' (bool)
    """

    if "title" not in recipe["file"]:
        raise KeyError("Recipe must have a title")

    recipe["title"] = recipe["file"]["title"]

    recipe["has_subtitle"] = False
    if recipe["file"].get("subtitle"):
        recipe["has_subtitle"] = True
        recipe["subtitle"] = recipe["file"]["subtitle"].lower()

    return recipe


def set_url(recipe):
    """Sets values regarding the URLs for the given recipe.

    Sets the following keys:
    - 'url_path' (str)
    - 'url' (str)
    - 'feedback_url' (str)
    """

    recipe["url_slug"] = utils.sluggify(recipe["file"]["folder_name"])
    recipe["url_path"] = "/" + recipe["url_slug"]
    recipe["url"] = utils.make_url(path=recipe["url_path"])
    recipe["feedback_url"] = utils.feedback_url(recipe["title"], recipe["url"])
    return recipe


def set_description(recipe):
    """Sets a flag indicating the presence of a recipe description.

    Sets the following keys:
    - 'has_description' (bool)
    """

    description = recipe["file"].get("description", "")
    if not isinstance(description, str):
        raise TypeError("Description must be a str.")

    recipe["has_description"] = bool(description)
    if description:
        recipe["description"] = description
    return recipe


def set_image(recipe):
    """Sets the image URL for the recipe.

    Sets the following keys:
    - 'has_image' (bool)
    - 'image_url' (str)
    """

    recipe["has_image"] = "image" in recipe
    if recipe["has_image"]:
        recipe["image_url"] = "/".join((recipe["url_slug"], recipe["image"]))
    else:
        recipe["image_url"] = "default.jpg"
    return recipe


def set_scales(recipe):
    """Sets scale-related values for each scale.

    Sets the following keys:
    - 'scales' (list)
    - 'has_scales' (bool)
    - 'base_select_class' (str)

    Sets the following keys for each scale:
    - 'label' (str)
    - 'item_class' (str)
    - 'select_class' (str)
    - 'button_class' (str)
    - 'js_function_name' (str)
    - 'keyboard_shortcut' (str)
    """

    recipe["scales"] = [{"multiplier": Fraction(1)}]
    for scale in recipe["file"].get("scale", []):
        recipe["scales"].append({"multiplier": _read_multiplier(scale)})
    # return scales

    for i, scale in enumerate(recipe["scales"], 1):
        label = str(scale["multiplier"].limit_denominator(100)).replace("/", "_") + "x"
        scale["label"] = label
        scale["item_class"] = f"scale-{label}"
        scale["select_class"] = f"display-scale-{label}"
        scale["button_class"] = f"display-scale-{label}-btn"
        scale["js_function_name"] = f"scale{label}"
        scale["keyboard_shortcut"] = i
    recipe["has_scales"] = len(recipe["scales"]) > 1
    recipe["base_select_class"] = recipe["scales"][0]["select_class"]
    return recipe


def _read_multiplier(scale) -> Fraction:
    """Returns multiplier of a scale."""

    if not isinstance(scale, (int, float, str, dict)):
        raise TypeError("Scale must be a dict or number.")

    if isinstance(scale, (int, float, str)):
        return parse.to_fraction(scale)

    # dict
    return parse.to_fraction(scale["multiplier"])


def set_times(recipe):
    """Set recipe attributes related to cook times.

    Sets the following keys for each scale:
    - 'times' (list)
    - 'has_times' (bool)

    Sets the following keys for each time:
    - 'unit' (str)
    - 'time_string' (str)
    """

    recipe["times"] = []

    for time in recipe["file"].get("times", []):
        recipe["times"].append(_read_time(time))

    for scale in recipe["scales"]:
        scale["times"] = recipe["times"]
        scale["has_times"] = bool(scale["times"])

    return recipe


def _read_time(time_data: dict) -> dict:
    """Formats a time entry."""

    if not isinstance(time_data, dict):
        raise TypeError("time must be a dict.")
    if "name" not in time_data:
        raise KeyError("time must have a name.")
    if not isinstance(time_data["name"], str):
        raise TypeError("time name must be a string.")
    if "time" not in time_data:
        raise KeyError("time must have a time.")
    if not isinstance(time_data["time"], (int, float)):
        raise TypeError(f'time time is a {type(time_data["time"])}, not a number.')
    if not isinstance(time_data.get("unit", ""), str):
        raise TypeError(f'time unit is a {type(time_data["unit"])}, not a string.')

    name = time_data["name"]
    time_time = parse.to_fraction(time_data["time"])
    default_unit = "minutes" if time_time > 1 else "minute"
    time = {
        "name": name,
        "time": time_time,
        "unit": time_data.get("unit", default_unit),
    }
    time["time_string"] = f'{parse.fraction_to_string(time_time)} {time["unit"]}'

    return time_data


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

    number = parse.fraction_to_string(yielb["number"])
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
            number_string = parse.fraction_to_string(number)
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
        ingredient["is_grocery"] = not ingredient["is_recipe"]
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
        elif parse.to_fraction(ingredient["scale"]) == multiplier:
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
        scaled["explicit_nutrition"] = nutrition.multiply(
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
        i_str.append(parse.fraction_to_string(ing["display_number"]))
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
        amount.append(parse.fraction_to_string(ingredient["display_number"]))
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
    grocery_item = grocery.lookup(ingredient["item"])

    if grocery_item is None:
        return

    ingredient["has_matching_grocery"] = True
    grocery_keys = [
        "grocery_id",
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
    ingredient["grocery"] = {k: grocery_item[k] for k in grocery_keys}
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

    count = ingredient["grocery"]["discrete_amount"]
    if count == 0:
        return 0

    return ingredient["number"] / count


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
                or parse.to_fraction(step["scale"]) == scale["multiplier"]
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


def set_sources(recipe: dict) -> dict:
    """Sets sources data.

    Sets the following keys:
    - 'has_sources' (bool)

    Sets the following keys for each source:
    - 'html' (str)
    """

    sources_data = recipe["file"].get("sources", [])
    if not isinstance(sources_data, (list)):
        raise TypeError("Sources must be a list.")

    recipe["sources"] = []
    for source_data in sources_data:
        recipe["sources"].append(_read_source(source_data))

    recipe["has_sources"] = bool(recipe["sources"])

    return recipe


def _read_source(source_data):
    """Returns formatted source data from input file."""

    name = source_data.get("name", "")
    url = source_data.get("url", "")
    if not isinstance(name, str):
        raise TypeError("Source name must be str.")
    if not isinstance(url, str):
        raise TypeError("Source url must be str.")
    if not name and not url:
        raise ValueError("Source must have name or url.")

    source = {}
    if name:
        source["name"] = name
    if url:
        source["url"] = url

    if name and url:
        source["html"] = f'<a href="{url}" target="_blank">{name}</a>'
    elif not name and url:
        source["html"] = f'<a href="{url}" target="_blank">{urlparse(url).netloc}</a>'
    else:  # name and not url:
        source["html"] = name

    return source


def set_notes(recipe):
    """Set notes for each scale.

    Sets the following keys for each scale:
    - 'notes' (list)
    - 'has_notes' (bool)
    - 'has_notes_box' (bool)
    """

    notes_data = recipe["file"].get("notes", [])
    if not isinstance(notes_data, list):
        raise TypeError("Notes must be a list.")

    recipe["notes"] = []
    for note_data in notes_data:
        recipe["notes"].append(_read_note(note_data))

    for scale in recipe["scales"]:
        scale["notes"] = notes_for_scale(recipe["notes"], scale)
        scale["has_notes"] = bool(scale["notes"])
        scale["has_notes_box"] = recipe["has_sources"] or scale["has_notes"]

    return recipe


def _read_note(note_data):
    """Returns formatted note data from input file."""

    if not isinstance(note_data, (dict, str)):
        raise TypeError("Note must be a dict or str.")
    if isinstance(note_data, str):
        return {"text": note_data}
    if "text" not in note_data:
        raise KeyError("Note must have text.")

    note = {"text": note_data["text"]}
    if "scale" in note_data:
        note["scale"] = parse.to_fraction(note_data["scale"])
    return note


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
    - 'videos_embedded' (list)
    - 'videos_linked' (list)
    - 'has_videos_embedded' (bool)
    - 'has_videos_linked' (bool)
    """

    videos_data = recipe["file"].get("videos", [])
    if not isinstance(videos_data, list):
        raise TypeError("Videos data must be a list.")

    recipe["videos_embedded"] = []
    recipe["videos_linked"] = []

    for video_data in videos_data:

        video = _read_video(video_data)

        url = video["url"]
        if utils.is_youtube_url(url):
            video_id = utils.youtube_url_id(url)
            recipe["videos_embedded"].append(
                {"url": url, "embed_url": utils.youtube_embed_url(video_id)}
            )
        else:
            recipe["videos_linked"].append({"url": url})

    recipe["has_videos_embedded"] = bool(recipe["videos_embedded"])
    recipe["has_videos_linked"] = bool(recipe["videos_linked"])
    return recipe


def _read_video(video_data):
    """Returns video from input data."""

    if not isinstance(video_data, dict):
        raise TypeError("Video data must be a dict.")
    if "url" not in video_data:
        raise KeyError("Video must have url.")
    if not isinstance(video_data["url"], str):
        raise TypeError("Video url must be a str.")
    if "list" in video_data and not isinstance(video_data["list"], str):
        raise TypeError("Video instruction_list must be a str.")

    video = {}
    video["url"] = video_data["url"]
    if "list" in video_data:
        video["list"] = video_data["list"]
    return video


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


def set_special_cases(recipe):
    """Checks input file for special cases."""

    if "cost" in recipe["file"]:
        recipe["explicit_cost"] = recipe["file"]["cost"]
    if "nutrition" in recipe["file"]:
        recipe["explicit_nutrition"] = nutrition.read(recipe["file"]["nutrition"])

    default_hide_cost = utils.config("default", "hide_cost", as_boolean=True)
    recipe["hide_cost"] = bool(recipe["file"].get("hide_cost", default_hide_cost))
    default_hide_nutrition = utils.config("default", "hide_nutrition", as_boolean=True)
    recipe["hide_nutrition"] = bool(
        recipe["file"].get("hide_nutrition", default_hide_nutrition)
    )

    return recipe
