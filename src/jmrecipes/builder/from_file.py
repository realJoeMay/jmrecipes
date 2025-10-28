"""Read recipe and collection files for build."""

import json
import yaml


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
    if file_path.endswith(".yaml"):
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
        return json.loads(data)
    if file_path.endswith(".yaml"):
        return yaml.safe_load(data)

    raise ValueError("file is not a valid format")
