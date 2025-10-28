"""Utilities to parse things."""

from math import floor
from fractions import Fraction
from typing import Tuple

from jmrecipes.utils import units


def ingredient(text: str) -> dict:
    """Parses an ingredient string into its component parts.

    This function takes a textual ingredient description (e.g., "1 cup chopped onions")
    and extracts four structured components:
      - number: the quantity (e.g., 1)
      - unit: the measurement unit (e.g., "cup")
      - item: the core ingredient name (e.g., "onions")
      - descriptor: any additional description or preparation info (e.g., "chopped")

    Parameters:
        text (str): The raw ingredient string to parse.

    Returns:
        dict: A dictionary with the following keys:
            - "number" (Fraction)
            - "unit" (str)
            - "item" (str)
            - "descriptor" (str)
    """

    number, other = _amount_and_other(text)
    unit, other = _unit_and_other(other)
    item, descriptor = _item_and_descriptor(other)
    return {"number": number, "unit": unit, "item": item, "descriptor": descriptor}


def to_fraction(number: int | float | str) -> Fraction:
    """Converts number to Fraction.

    Args:
        number: Number or number-like string. String can include mixed
        numbers and unicode fractions.

    Returns:
        Number as a Fraction object.
    """

    if not isinstance(number, (int, float, str)):
        raise TypeError

    if isinstance(number, (int, float)):
        return Fraction(number)

    # str
    amount, remaining = _split_fraction_amount_and_text(number)
    if remaining:
        raise ValueError(f"{number} is not a number.")

    return amount


def fraction_to_string(frac: Fraction, to_unicode: bool = True) -> str:
    """Converts Fraction to a nice string."""

    whole = floor(frac)
    (num, den) = (frac - whole).as_integer_ratio()

    amount_parts = []
    if whole:
        amount_parts.append(str(whole))
    if num:
        amount_parts.append(f"{num}/{den}")

    amount_display = " ".join(amount_parts)

    if not to_unicode:
        return amount_display

    for asci, unicode in _unicode_fractions.items():
        # remove space if mixed number
        amount_display = amount_display.replace(" " + asci, unicode)
        # replaces if no leading integer
        amount_display = amount_display.replace(asci, unicode)
    return amount_display


def _amount_and_other(text, amount_as_str=False) -> Tuple[Fraction | str, str]:
    """Splits a text string into an amount and the remaining text.

    It recognizes Unicode vulgar fractions and converts them to ASCII
    equivalents.

    Args:
        text (str): The input text, e.g., "1½ cups flour".
        amount_as_str (bool): If True, return the amount as a formatted
        string (e.g., '1 1/2').

    Returns:
        Tuple[Union[Fraction, str], str]: The numeric part (as Fraction
        or string) and the remaining text.
    """

    if amount_as_str:
        return _split_string_amount_and_text(text)

    return _split_fraction_amount_and_text(text)


def _split_string_amount_and_text(text) -> Tuple[str, str]:
    amount, text = _split_fraction_amount_and_text(text)
    return fraction_to_string(amount), text


def _split_fraction_amount_and_text(text) -> Tuple[Fraction, str]:

    # replace "1½" with "1 1/2"
    for asci, unicode in _unicode_fractions.items():
        text = text.replace(unicode, " " + asci)

    amount = Fraction()
    words = text.split()
    remaining_words = []
    for i, word in enumerate(words):
        try:
            amount += Fraction(word)
        except ValueError:
            remaining_words = words[i:]
            break

    return amount, " ".join(remaining_words)


def _unit_and_other(text: str) -> tuple[str, str]:
    """Splits a string into a unit and the remaining text.

    This function attempts to extract the longest prefix from the
    beginning of the input string that matches a known unit. The rest
    of the string is returned as the remaining text.

    For example, given "tablespoons sugar", it might return
    ("tablespoons", "sugar").

    Args:
        text (str): The input string containing a unit followed by
        additional text.

    Returns:
        tuple[str, str]: A tuple containing:
            - The matched unit (or empty string if no unit is found).
            - The remaining portion of the input text.
    """

    words = text.split()

    for i in range(len(words), 0, -1):
        candidate = " ".join(words[:i])
        if units.is_unit(candidate):
            return candidate, " ".join(words[i:])

    # No unit found
    return "", text


def _item_and_descriptor(text: str) -> tuple[str, str]:
    """Splits an ingredient string into the main ingredient and its
    description.

    This function separates a descriptive note from the main ingredient
    text. It checks for two possible patterns:

    1. A parenthetical comment at the end.
    2. A comma-separated description at the end.

    If neither is found, the entire input is returned as the ingredient
    with an empty description.

    Args:
        text (str): A string representing a single ingredient line.

    Returns:
        tuple[str, str]: A tuple where the first element is the main
        ingredient, and the second is a description or note (if any).
    """

    if "(" in text and text.endswith(")"):
        last_open = text.rfind("(")
        parenthetical = text[last_open + 1 : -1]
        main = text[:last_open].strip()
        return main, parenthetical

    if ", " in text:
        last_comma = text.rfind(", ")
        return text[:last_comma], text[last_comma + 2 :]

    return text, ""


_unicode_fractions = {
    "1/4": "¼",
    "1/2": "½",
    "3/4": "¾",
    "1/7": "⅐",
    "1/9": "⅑",
    "1/10": "⅒",
    "1/3": "⅓",
    "2/3": "⅔",
    "1/5": "⅕",
    "2/5": "⅖",
    "3/5": "⅗",
    "4/5": "⅘",
    "1/6": "⅙",
    "5/6": "⅚",
    "1/8": "⅛",
    "3/8": "⅜",
    "5/8": "⅝",
    "7/8": "⅞",
}
