import os
import pandas as pd


# Directories
utils_directory = os.path.dirname(os.path.abspath(__file__))
src_directory = os.path.split(utils_directory)[0]
project_directory = os.path.split(src_directory)[0]
data_directory = os.path.join(project_directory, "data")


def lookup(ingredient_name: str) -> dict | None:
    """Look up grocery information for a given ingredient name.

    This function searches the `_groceries` DataFrame for a row
    matching the lowercase version of the provided ingredient name.
    If found, it returns the row as a dictionary.

    Args:
        ingredient_name (str): The name of the ingredient to look up.

    Returns:
        dict | None: A dictionary containing grocery info if a match
        is found, otherwise None.
    """

    search_name = ingredient_name.lower()
    matching_items = _groceries[_groceries.name == search_name]

    if matching_items.empty:
        return None

    matching_item = matching_items.iloc[0]
    grocery_dict = matching_item.to_dict()

    return grocery_dict


def _load_groceries():
    groceries_path = os.path.join(data_directory, "groceries.xlsx")
    groceries = pd.read_excel(groceries_path)
    column_defaults = {
        "name": "",
        "category": "",
        "url": "",
        "cost": 0,
        "volume_amount": 0,
        "volume_unit": "",
        "weight_amount": 0,
        "weight_unit": "",
        "other_amount": 0,
        "other_unit": "",
        "discrete_amount": 0,
        "calories": 0,
        "fat": 0,
        "carbohydrates": 0,
        "protein": 0,
        "tags": "",
        "notes": "",
    }
    groceries.fillna(value=column_defaults, inplace=True)
    return groceries


_groceries = _load_groceries()
