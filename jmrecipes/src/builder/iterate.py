"""Utilities to iterate over the build structure."""

from typing import Optional


def scales_in(container, include=None):
    """Returns a list of recipe scales from the container."""

    if include is None:
        include = ""

    scales = []
    for recipe in _container_to_recipes(container):
        for scale in recipe["scales"]:
            item_list = []
            if "r" in include:
                item_list.append(recipe)
            item_list.append(scale)

            if len(item_list) == 1:
                scales.append(item_list[0])
            else:
                scales.append(tuple(item_list))

    return scales


def ingredients_in(
    container: dict | list,
    keys: Optional[str | list] = None,
    values: Optional[dict] = None,
    include: Optional[str] = None,
) -> list:
    """Returns a list of ingredients from the container.

    This function extracts scaled ingredients from a recipe, list of
    recipes, or site. The `include` parameter determines whether the
    recipe and scale information should be included in the returned
    list.

    Args:
        container (dict, list): The data containing ingredients. Can be
        a site dictionary, list of recipe dictionaries, or a recipe
        dictionary.

        keys (str or list, optional): A key or a list of keys that an
            ingredient must have to be on the returned list. Default to
            None, meaning there is no filter by keys.

        values (dict, optional): A dictionary of key value pairs that
            an ingredient must have to be on the returned list.
            Default is None, meaning there is no filter by key-value
            pair.

        include (str, optional): A string that specifies what
            additional information to include in the returned tuples.
            If 'r' is included, the recipe information is included. If
            's' is included, the scale information is included.
            Defaults to None, meaning only the ingredient information
            is included.

    Returns:
        list: A list of ingredient dictionaries, or a list of tuples
        containing optional recipe and scale information. If 'r' is in
        `include`, the recipe dictionary is included in each tuple. If
        's' is in `include`, the scale dictionary is included in each
        tuple. The order of items in the tuple is (recipe, scale,
        ingredient).
    """

    if values is None:
        values = {}
    if include is None:
        include = ""
    if keys is None:
        keys = []
    if isinstance(keys, str):
        keys = [keys]

    ingredients = []
    for recipe in _container_to_recipes(container):
        for scale in recipe["scales"]:
            for ingredient in scale["ingredients"]:
                if _ingredient_matches_criteria(ingredient, keys, values):
                    item_list = []
                    if "r" in include:
                        item_list.append(recipe)
                    if "s" in include:
                        item_list.append(scale)
                    item_list.append(ingredient)

                    if len(item_list) == 1:
                        ingredients.append(item_list[0])
                    else:
                        ingredients.append(tuple(item_list))

    return ingredients


def _container_to_recipes(container) -> list:
    """Returns a list of recipes from the container.

    This function extracts scaled ingredients from a recipe, list of
    recipes, or site. The `include` parameter determines whether the
    recipe and scale information should be included in the returned
    list.

    Args:
        container (dict, list): Can be a site dictionary, list of
        recipe dictionaries, or a recipe dictionary.

    Returns:
        list: A list of recipe dictionaries.
    """

    if "recipes" in container.keys():
        return container["recipes"]
    elif isinstance(container, list):
        return container
    else:
        return [container]


def _ingredient_matches_criteria(ingredient: dict, keys: list, values: dict) -> bool:
    """Checks if ingredient has keys and matches values.

    Args:
        ingredient (dict): The ingredient to be checked.
        keys (list): A list of keys that must be present in the
            ingredient.
        values (dict): A dictionary of key-value pairs that must match
            in the ingredient.

    Returns:
        bool: True if the ingredient contains all keys and matches all
            the values, False otherwise.
    """

    for key in keys + list(values.keys()):
        if key not in ingredient:
            return False
    for k, v in values.items():
        if ingredient[k] != v:
            return False
    return True
