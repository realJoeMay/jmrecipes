import os
import pandas as pd

from jmrecipes.utils import parse


# Directories
utils_directory = os.path.dirname(os.path.abspath(__file__))
jmr_directory = os.path.split(utils_directory)[0]
src_directory = os.path.split(jmr_directory)[0]
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

    # search_name = ingredient_name.lower()
    matching_items = _groceries[_groceries.name.str.lower() == ingredient_name.lower()]

    if matching_items.empty:
        return None

    matching_item = matching_items.iloc[0]
    grocery_dict = matching_item.to_dict()

    return grocery_dict


def full_list() -> list[dict]:
    """Return list of all loaded groceries."""
    return _groceries.to_dict(orient="records")


def _load_groceries():
    groceries_path = os.path.join(data_directory, "groceries.xlsx")
    groceries = pd.read_excel(groceries_path)

    # fill empty cells
    defaults = {
        "name": "",
        "plural": "",
        "category": "",
        "url": "",
        "cost": 0,
        "volume": "",
        "weight": "",
        "other": "",
        "count": 0,
        "calories": 0,
        "fat": 0,
        "carbohydrates": 0,
        "protein": 0,
        "tags": "",
        "notes": "",
    }
    groceries.fillna(value=defaults, inplace=True)
    groceries.index = groceries.index + 1
    groceries.index.name = "grocery_id"
    groceries = groceries.reset_index()

    # split amount into number and unit columns (volume => volume_number, volume_unit)
    for unit_type in ["volume", "weight", "other"]:
        groceries[[unit_type + "_amount", unit_type + "_unit"]] = groceries[
            unit_type
        ].apply(lambda x: pd.Series(parse.amount(x)))

    # transform to include singular and plural items
    singular_rows = groceries.assign(singular="")
    plural_rows = groceries[groceries["plural"] != ""].copy()
    plural_rows["name"], plural_rows["singular"] = (
        plural_rows["plural"],
        plural_rows["name"],
    )
    result = pd.concat([singular_rows, plural_rows], ignore_index=True)

    # move singular column from end to position 2
    cols = list(result.columns)
    cols.insert(2, cols.pop(cols.index("singular")))
    result = result[cols]

    # print(result.to_string(index=False))
    return result


_groceries = _load_groceries()
