from configparser import ConfigParser
from fractions import Fraction
import json
from math import floor
import os
import shutil
from urllib.parse import urlparse, urlunparse, urlencode, parse_qs
from typing import Union, Tuple
import pandas as pd

from segno import make_qr


# Directories
utils_directory = os.path.dirname(os.path.abspath(__file__))
src_directory = os.path.split(utils_directory)[0]
project_directory = os.path.split(src_directory)[0]
builds_directory = os.path.join(project_directory, "builds")
data_directory = os.path.join(project_directory, "data")
assets_directory = os.path.join(data_directory, "assets")
templates_directory = os.path.join(src_directory, "templates")


def create_dir(path):
    """Create a folder."""

    if not os.path.exists(path):
        os.mkdir(path)


def make_empty_dir(path):
    """Create a folder. Empty folder if already exists."""

    create_dir(path)
    # shutil.rmtree(path)
    create_dir(path)


def write_file(content: str, path: str):
    """Save content to a text file."""

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def write_json_file(data: dict, path: str):
    """Save dictionary data to a JSON file.

    Args:
        data: Dictionary of data to write.
        path: File path
    """

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, cls=JMREncoder)


class JMREncoder(json.JSONEncoder):
    """Extends JSONEncoder to work with Fraction objects.

    More info:
    https://dev.to/kfuquay/extending-pythons-json-encoder-7k0
    """

    def default(self, o):
        if isinstance(o, Fraction):
            o = str(o) + " <Fraction>"
            return o

        # Default behavior for all other types
        return super().default(o)


# Config data


def config(section: str, name: str, as_boolean: bool = False) -> Union[str, bool]:
    """Read string from config file."""

    config_path = os.path.join(data_directory, "config.ini")
    parser = ConfigParser()
    parser.read(config_path)
    if as_boolean:
        return parser.getboolean(section, name)
    return parser.get(section, name)


def site_title() -> str:
    """Read site title from config file."""

    return str(config("site", "title"))


def site_domain() -> str:
    """Read site domain from config file."""

    return str(config("site", "domain"))


# def config_feedback_url() -> str:
#     """Read feedback url from config file."""

#     return config('feedback', 'url')


# Templates


def split_unit_and_text(text: str) -> tuple[str, str]:
    """
    Splits a string into a unit and the remaining text.

    This function attempts to extract the longest prefix from the beginning of
    the input string that matches a known unit. The rest of the string is returned as the remaining text.

    For example, given "tablespoons sugar", it might return ("tablespoons", "sugar").

    Args:
        text (str): The input string containing a unit followed by additional text.

    Returns:
        tuple[str, str]: A tuple containing:
            - The matched unit (or an empty string if no unit is found).
            - The remaining portion of the input text.
    """

    words = text.split()

    for i in range(len(words), 0, -1):
        candidate = " ".join(words[:i])
        if is_unit(candidate):
            return candidate, " ".join(words[i:])

    # No unit found
    return "", text


# Fractions
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


def to_fraction(number: Union[int, float, str]) -> Fraction:
    """Converts number to Fraction.

    Args:
        number: Number or number-like string. String can include mixed numbers and unicode fractions.

    Returns:
        Number as a Fraction object.
    """

    if not isinstance(number, (int, float, str)):
        raise TypeError

    if isinstance(number, (int, float)):
        return Fraction(number)

    # str
    amount, remaining = split_amount_and_text(number)
    if remaining:
        raise ValueError(f"{number} is not a number.")

    return amount


def split_amount_and_text(
    text, amount_as_str=False
) -> Tuple[Union[Fraction, str], str]:
    """
    Splits a text string into a numeric amount and the remaining text.

    It recognizes Unicode vulgar fractions and converts them to ASCII equivalents.

    Args:
        text (str): The input text, e.g., "1½ cups flour".
        amount_as_str (bool): If True, return the amount as a formatted string (e.g., '1 1/2').

    Returns:
        Tuple[Union[Fraction, str], str]: The numeric part (as Fraction or string) and the
        remaining text.
    """

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

    if amount_as_str:
        amount = fraction_to_string(amount)

    return amount, " ".join(remaining_words)


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


def format_currency(cost: Union[int, float]) -> str:
    """Formats a cost value as a currency string.

    This function converts a numeric cost value into a string formatted as currency.
    The cost is rounded to two decimal places and prefixed with a dollar sign.
    """

    return "${:.2f}".format(float(cost))


# URLs
def make_url(
    scheme=None, domain=None, path=None, params=None, query=None, fragment=None
) -> str:
    """Constructs a URL from components.

    Args:
        scheme (str, optional): The URL scheme. Defaults to 'https'.
        domain (str, optional): The domain name of the URL. Defaults to the  `site_domain` from config file.
        path (str, optional): The path component of the URL. Defaults to an empty string.
        params (str, optional): The parameters component of the URL. Defaults to an empty string.
        query (dict, optional): The query parameters as a dictionary. If provided, it is URL-encoded.
        fragment (str, optional): The fragment component of the URL. Defaults to an empty string.

    Returns:
        str: The constructed URL as a string.
    """

    if scheme is None:
        scheme = "https"
    if domain is None:
        domain = config("site", "domain")
    if path is None:
        path = ""
    if params is None:
        params = ""
    if fragment is None:
        fragment = ""
    if query is None:
        query = ""
    else:
        query = urlencode(query)
    return urlunparse([scheme, domain, path, params, query, fragment])


def feedback_url(page_name: str, source_url: str) -> str:
    """Create feedback url with prefilled values."""

    components = urlparse(config("feedback", "url"))
    query = {"prefill_page": page_name, "prefill_source_url": source_url}
    return make_url(domain=components[1], path=components[2], query=query)


def sluggify(name: str) -> str:
    """Converts name to url slug preferred format.

    Slug preferred format has lower-case ascii, digits, and dash "-".
    - Upper case letters converted to lower case
    - Spaces and underscores are replaced with dashes
    - Invalid characters are removed
    - Any double dashes are removed
    """

    slug = name.lower()
    slug = slug.replace(" ", "-")
    slug = slug.replace("_", "-")

    valid = "abcdefghijklmnopqrstuvwxyz0123456789-"
    for c in slug:
        if c not in valid:
            slug = slug.replace(c, "")

    while "--" in slug:
        slug = slug.replace("--", "-")

    return name


def is_youtube_url(url: str) -> bool:

    return _is_youtube_full_url(url) or _is_youtube_short_url(url)


def youtube_url_id(url: str) -> str:
    """Returns youtube video ID from url."""

    if _is_youtube_full_url(url):
        return _youtube_full_url_id(url)
    elif _is_youtube_short_url(url):
        return _youtube_short_url_id(url)
    raise Exception(f"Cannot get youtube video ID from url: {url}")


def youtube_embed_url(video_id: str) -> str:
    """Returns embed url for a youtube video."""

    return f'<iframe src="https://www.youtube.com/embed/{video_id}" allowfullscreen></iframe>'


def _is_youtube_full_url(url: str) -> bool:

    return "youtube.com/watch" in url


def _is_youtube_short_url(url: str) -> bool:

    return "youtu.be/" in url


def _youtube_full_url_id(url: str) -> str:
    """Returns youtube video ID from full url."""

    parsed_url = urlparse(url)
    query_string = parsed_url.query
    query_params = parse_qs(query_string)
    return query_params["v"][0]


def _youtube_short_url_id(url: str) -> str:
    """Returns youtube video ID from short url."""

    parsed_url = urlparse(url)
    path = parsed_url.path
    return path.strip("/")


# Pipe
def pipe(data: dict, log_path: str, *funcs) -> dict:
    """Pipe data through a sequence of functions.

    Optionally saves data after each function in log files. Saves
    no log if log_path is empty string.
    """

    has_log = log_path != ""

    if has_log:
        create_dir(log_path)
        log_file_path = os.path.join(log_path, "0_start.json")
        write_json_file(data, log_file_path)

    for i, func in enumerate(funcs, 1):
        data = func(data)
        if has_log:
            log_file_path = os.path.join(log_path, f"{i}_{func.__name__}.json")
            write_json_file(data, log_file_path)

    return data


# Groceries


def grocery_info(ingredient_name):
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


# Qr codes
def make_qr_file(link: str, filepath: str) -> None:
    """Create and save QR code."""

    qr_code = make_qr(link)
    qr_code.save(filepath, scale=5, border=0)


def split_ingredient_and_description(text: str) -> tuple[str, str]:
    """Splits an ingredient string into the main ingredient and its description.

    This function separates a descriptive note from the main ingredient text.
    It checks for two possible patterns:

    1. A parenthetical comment at the end (e.g., "flour (sifted)") — returns "flour" and "sifted".
    2. A comma-separated description at the end (e.g., "sugar, divided") — returns "sugar" and
        "divided".

    If neither is found, the entire input is returned as the ingredient with an empty description.

    Args:
        text (str): A string representing a single ingredient line.

    Returns:
        tuple[str, str]: A tuple where the first element is the main ingredient,
                         and the second is a description or note (if any).
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


def ingredients_in(
    container: dict | list,
    keys: str | list = None,
    values: dict = None,
    include: str = None,
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
    for recipe in container_to_recipes(container):
        for scale in recipe["scales"]:
            for ingredient in scale["ingredients"]:
                if ingredient_matches_criteria(ingredient, keys, values):
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


def container_to_recipes(container) -> list:
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


def ingredient_matches_criteria(ingredient: dict, keys: list, values: dict) -> bool:
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


def scales_in(container, include=None):
    """Returns a list of recipe scales from the container."""

    if include is None:
        include = ""

    scales = []
    for recipe in container_to_recipes(container):
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


def multiply_nutrition(nutrition, multiplier, round_result=False) -> dict:
    """Multiplies nutrition values by a given multiplier.

    Optionally, the results can be rounded to the nearest integer.
    """

    multiplied = {
        "calories": nutrition["calories"] * multiplier,
        "fat": nutrition["fat"] * multiplier,
        "carbohydrates": nutrition["carbohydrates"] * multiplier,
        "protein": nutrition["protein"] * multiplier,
    }

    if round_result:
        multiplied = {
            "calories": round(multiplied["calories"]),
            "fat": round(multiplied["fat"]),
            "carbohydrates": round(multiplied["carbohydrates"]),
            "protein": round(multiplied["protein"]),
        }

    return multiplied
