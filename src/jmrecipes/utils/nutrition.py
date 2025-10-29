"""Nutrition."""


def read(nutrition_data: dict) -> dict:
    """Formats nutrition data from input file."""

    return {
        "calories": nutrition_data.get("calories", 0),
        "fat": nutrition_data.get("fat", 0),
        "protein": nutrition_data.get("protein", 0),
        "carbohydrates": nutrition_data.get("carbohydrates", 0),
    }


def multiply(
    nutrition: dict,
    multiplier: int | float,
    round_result: bool = False,
) -> dict:
    """
    Multiplies each nutrition value by a given multiplier.

    Parameters:
        nutrition (dict[str, int | float]): A dictionary of nutrition values
            (e.g., {"calories": 100, "fat": 2.5, ...}).
        multiplier (int | float): The number to multiply each value by.
        round_result (bool, optional): If True, round each result to the nearest integer.

    Returns:
        dict[str, int | float]: A new dictionary with the scaled nutrition values.
    """
    multiplied = {key: value * multiplier for key, value in nutrition.items()}

    if round_result:
        multiplied = {key: round(value) for key, value in multiplied.items()}

    return multiplied
