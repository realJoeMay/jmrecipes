"""Read recipe and collection files for build."""

import json
from fractions import Fraction
import yaml

from src.utils import utils


def collection(file_path: str) -> dict:
    """Converts a collection data file to a collection dictionary.

    Args:
        file_path: Str path to collection data file.

    Returns:
        Dict containing collection data.
    """

    with open(file_path, "r", encoding="utf8") as f:
        data = f.read()

    if file_path.endswith(".json"):
        return json.loads(data)
    elif file_path.endswith(".yaml"):
        return yaml.safe_load(data)

    raise ValueError("file is not a valid format")


def recipe(file_path: str) -> dict:
    """Converts a recipe data file to a recipe dictionary.

    Args:
        filepath: Str path to recipe data file.

    Returns:
        Dict containing recipe data.
    """

    with open(file_path, "r", encoding="utf8") as f:
        data = f.read()

    if file_path.endswith(".json"):
        return _recipe_dict(json.loads(data))
    if file_path.endswith(".yaml"):
        return _recipe_dict(yaml.safe_load(data))

    raise ValueError("file is not a valid format")


def _recipe_dict(data: dict) -> dict:
    """Restructures input dictionary to creates recipe dictionary.

    Args:
        data: Recipe input data as dictionary.

    Returns:
        Recipe data dictionary.
    """

    loaded_recipe = {}
    loaded_recipe["title"] = _read_title(data)
    loaded_recipe["subtitle"] = data.get("subtitle", "")
    loaded_recipe["times"] = _read_times(data)
    loaded_recipe["yield"] = _read_yield(data)
    loaded_recipe["ingredients"] = _read_ingredients(data)
    loaded_recipe["instructions"] = _read_instructions(data)
    loaded_recipe["scales"] = _read_scales(data)
    loaded_recipe["videos"] = _read_videos(data)

    if "description" in data:
        loaded_recipe["description"] = data["description"]
    if "cost" in data:
        loaded_recipe["explicit_cost"] = data["cost"]
    if "nutrition" in data:
        loaded_recipe["explicit_nutrition"] = _read_nutrition(data["nutrition"])
    if "hide_cost" in data:
        loaded_recipe["hide_cost"] = bool(data["hide_cost"])
    if "hide_nutrition" in data:
        loaded_recipe["hide_nutrition"] = bool(data["hide_nutrition"])
    if "sources" in data:
        loaded_recipe["sources"] = _read_sources(data)
    if "notes" in data:
        loaded_recipe["notes"] = _read_notes(data)

    return loaded_recipe


def _read_title(data):
    """Returns recipe title from input file."""

    if "title" not in data:
        raise KeyError("Recipe must have a title")

    return data["title"]


def _read_times(data):
    """Sets time data from input file."""

    times = []
    for time in data.get("times", []):
        times.append(_read_time(time))
    return times


def _read_time(time: dict) -> dict:
    """Formats a time entry."""

    if not isinstance(time, dict):
        raise TypeError("time must be a dict.")
    if "name" not in time:
        raise KeyError("time must have a name.")
    if not isinstance(time["name"], str):
        raise TypeError("time name must be a string.")
    if "time" not in time:
        raise KeyError("time must have a time.")
    if not isinstance(time["time"], (int, float)):
        raise TypeError(f'time time is a {type(time["time"])}, not a number.')
    if not isinstance(time.get("unit", ""), str):
        raise TypeError(f'time unit is a {type(time["unit"])}, not a string.')

    name = time["name"]
    time_time = utils.to_fraction(time["time"])
    time_data = {"name": name, "time": time_time, "unit": time.get("unit", "")}
    return time_data


def _read_yield(data):
    """Sets yield data from input file."""

    if "yield" not in data:
        return []

    yield_data = data["yield"]

    if not isinstance(yield_data, (int, float, list)):
        raise TypeError("Yield data must be a number or a list.")

    if isinstance(yield_data, (int, float)):
        return [{"number": yield_data}]

    # list
    yields = []
    for yield_item in data["yield"]:
        yields.append(_read_yield_item(yield_item))
    return yields


def _read_yield_item(data):
    """Formats yield data from input file."""

    if "number" not in data:
        raise KeyError("Yield data must have number field.")

    yielb = {}
    yielb["number"] = utils.to_fraction(data["number"])
    if "unit" in data:
        yielb["unit"] = data["unit"]
    if "show_yield" in data:
        yielb["show_yield"] = bool(data["show_yield"])
    if "show_serving_size" in data:
        yielb["show_serving_size"] = bool(data["show_serving_size"])

    return yielb


def _read_ingredients(data):
    """Sets ingredients data from input file."""

    ingredients = []
    for ingredient in data.get("ingredients", []):
        ingredients.append(_read_ingredient(ingredient))
    return ingredients


def _read_ingredient(data: dict) -> dict:
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

    # read from 'text' field
    if "text" in data:
        ingredient["number"], remainder = utils.split_amount_and_text(data["text"])
        ingredient["unit"], remainder = utils.split_unit_and_text(remainder)
        ingredient["item"], ingredient["descriptor"] = (
            utils.split_ingredient_and_description(remainder)
        )

    # read number fields
    for field in ["number", "display_number"]:
        if field in data:
            ingredient[field] = utils.to_fraction(data[field])

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
        if field in data:
            ingredient[field] = data[field]

    # read fields that change name
    if "cost" in data:
        ingredient["explicit_cost"] = data["cost"]
    if "nutrition" in data:
        ingredient["explicit_nutrition"] = _read_nutrition(data["nutrition"])
    if "recipe" in data:
        ingredient["recipe_slug"] = data["recipe"]

    return ingredient


def _read_instructions(data):
    """Sets instructions data from input file."""

    instructions = []
    for step in data.get("instructions", []):
        instructions.append(_read_step(step))
    return instructions


def _read_step(data):
    """Formats instructions data from input file."""

    if not isinstance(data, (str, dict)):
        raise TypeError("Instructions step must be a string or dictionary.")

    if isinstance(data, dict) and "text" not in data:
        raise KeyError('Instructions step must include "text" field.')

    if isinstance(data, str):
        return {"text": data}

    # data is dict with 'text'
    step = {"text": data["text"]}
    if "scale" in data:
        step["scale"] = data["scale"]
    if "list" in data:
        step["list"] = data["list"]
    return step


def _read_scales(data):
    """Formats scale data from input file, including base scale."""

    scales = [{"multiplier": Fraction(1)}]
    for scale in data.get("scale", []):
        scales.append({"multiplier": _read_multiplier(scale)})
    return scales


def _read_multiplier(scale) -> Fraction:
    """Returns multiplier of a scale."""

    if not isinstance(scale, (int, float, str, dict)):
        raise TypeError("Scale must be a dict or number.")

    if isinstance(scale, (int, float, str)):
        return utils.to_fraction(scale)

    # dict
    return utils.to_fraction(scale["multiplier"])


def _read_videos(data):
    """Returns videos from input data."""

    if "video" not in data:
        return []
    if not isinstance(data["video"], list):
        raise TypeError("Videos data must be a list.")

    return [_read_video(d) for d in data["video"]]


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


def _read_nutrition(nutrition):
    """Formats nutrition data from input file."""

    return {
        "calories": nutrition.get("calories", 0),
        "fat": nutrition.get("fat", 0),
        "protein": nutrition.get("protein", 0),
        "carbohydrates": nutrition.get("carbohydrates", 0),
    }


def _read_sources(data):
    """Returns sources data from input dictionary."""

    sources_data = data["sources"]
    if not isinstance(sources_data, (list)):
        raise TypeError("Sources must be a list.")

    sources = []
    for source in sources_data:
        sources.append(_read_source(source))

    return sources


def _read_source(source):
    """Returns formatted source data from input file."""

    out = {}
    if "name" in source and source["name"]:
        out["name"] = source["name"]
    if "url" in source:
        out["url"] = source["url"]
    return out


def _read_notes(data):
    """Returns notes data from input dictionary."""

    notes_data = data["notes"]
    if not isinstance(notes_data, list):
        raise TypeError("Notes must be a list.")

    notes = []
    for note in notes_data:
        notes.append(_read_note(note))
    return notes


def _read_note(note_data):
    """Returns formatted note data from input file."""

    if not isinstance(note_data, dict):
        raise TypeError("Note must be a dictionary.")
    if "text" not in note_data:
        raise KeyError("Note must have text.")

    note = {"text": note_data["text"]}
    if "scale" in note_data:
        note["scale"] = utils.to_fraction(note_data["scale"])
    return note
