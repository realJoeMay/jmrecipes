from configparser import ConfigParser
from fractions import Fraction
from jinja2 import Environment, FileSystemLoader
from json import JSONEncoder
import json
from math import floor
import os
import pandas as pd
from segno import make_qr
import shutil
from urllib.parse import urlparse, urlunparse, urlencode


# Directories
src_directory = os.path.dirname(os.path.abspath(__file__))
project_directory = os.path.split(src_directory)[0]
builds_directory = os.path.join(project_directory, 'builds')
data_directory = os.path.join(project_directory, 'data')
assets_directory = os.path.join(data_directory, 'assets')
templates_directory = os.path.join(src_directory, 'templates')


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

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def write_json_file(data: dict, path: str):
    """Save dictionary data to a JSON file.

    Args:
        data: Dictionary of data to write.
        path: File path 
    """

    with open(path, 'w') as f:
        json.dump(data, f, indent=4, cls=jmrEncoder)


class jmrEncoder(JSONEncoder):
    """Extends JSONEncoder to work with Fraction objects.
    
    More info:
    https://dev.to/kfuquay/extending-pythons-json-encoder-7k0
    """

    def default(self, obj):
        if isinstance(obj, Fraction):
            obj = obj.__str__() + ' <Fraction>'
            return obj

        # Default behavior for all other types
        return super().default(obj)



# Config data

def config(section: str, name: str, as_boolean: bool = False) -> (str | bool):
    """Read string from config file."""

    config_path = os.path.join(data_directory, 'config.ini')
    parser = ConfigParser()
    parser.read(config_path)
    if as_boolean:
        return parser.getboolean(section, name)
    return parser.get(section, name)


def site_title() -> str:
    """Read site title from config file."""

    return config('site', 'title')


def site_domain() -> str:
    """Read site domain from config file."""

    return config('site', 'domain')


# def config_feedback_url() -> str:
#     """Read feedback url from config file."""

#     return config('feedback', 'url')


# Templates

def render_template(template_name: str, **context):
    """Renders template with context."""

    environment = Environment(loader=FileSystemLoader(templates_directory))
    template = environment.get_template(template_name)
    return template.render(context)


# icons
class icon:
    """Class for handling svg icons."""

    gear = "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 512 512'><!--! Font Awesome Pro 6.2.0 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license (Commercial License) Copyright 2022 Fonticons, Inc. --><path d='M495.9 166.6c3.2 8.7 .5 18.4-6.4 24.6l-43.3 39.4c1.1 8.3 1.7 16.8 1.7 25.4s-.6 17.1-1.7 25.4l43.3 39.4c6.9 6.2 9.6 15.9 6.4 24.6c-4.4 11.9-9.7 23.3-15.8 34.3l-4.7 8.1c-6.6 11-14 21.4-22.1 31.2c-5.9 7.2-15.7 9.6-24.5 6.8l-55.7-17.7c-13.4 10.3-28.2 18.9-44 25.4l-12.5 57.1c-2 9.1-9 16.3-18.2 17.8c-13.8 2.3-28 3.5-42.5 3.5s-28.7-1.2-42.5-3.5c-9.2-1.5-16.2-8.7-18.2-17.8l-12.5-57.1c-15.8-6.5-30.6-15.1-44-25.4L83.1 425.9c-8.8 2.8-18.6 .3-24.5-6.8c-8.1-9.8-15.5-20.2-22.1-31.2l-4.7-8.1c-6.1-11-11.4-22.4-15.8-34.3c-3.2-8.7-.5-18.4 6.4-24.6l43.3-39.4C64.6 273.1 64 264.6 64 256s.6-17.1 1.7-25.4L22.4 191.2c-6.9-6.2-9.6-15.9-6.4-24.6c4.4-11.9 9.7-23.3 15.8-34.3l4.7-8.1c6.6-11 14-21.4 22.1-31.2c5.9-7.2 15.7-9.6 24.5-6.8l55.7 17.7c13.4-10.3 28.2-18.9 44-25.4l12.5-57.1c2-9.1 9-16.3 18.2-17.8C227.3 1.2 241.5 0 256 0s28.7 1.2 42.5 3.5c9.2 1.5 16.2 8.7 18.2 17.8l12.5 57.1c15.8 6.5 30.6 15.1 44 25.4l55.7-17.7c8.8-2.8 18.6-.3 24.5 6.8c8.1 9.8 15.5 20.2 22.1 31.2l4.7 8.1c6.1 11 11.4 22.4 15.8 34.3zM256 336c44.2 0 80-35.8 80-80s-35.8-80-80-80s-80 35.8-80 80s35.8 80 80 80z'/></svg>"
    x = '<svg xmlns="http://www.w3.org/2000/svg" height="1em" viewBox="0 0 320 512"><!--! Font Awesome Pro 6.2.0 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license (Commercial License) Copyright 2022 Fonticons, Inc. --><path d="M310.6 150.6c12.5-12.5 12.5-32.8 0-45.3s-32.8-12.5-45.3 0L160 210.7 54.6 105.4c-12.5-12.5-32.8-12.5-45.3 0s-12.5 32.8 0 45.3L114.7 256 9.4 361.4c-12.5 12.5-12.5 32.8 0 45.3s32.8 12.5 45.3 0L160 301.3 265.4 406.6c12.5 12.5 32.8 12.5 45.3 0s12.5-32.8 0-45.3L205.3 256 310.6 150.6z"/></svg>'
    home = '<svg xmlns="http://www.w3.org/2000/svg" height="1em" viewBox="0 0 448 512"><!--! Font Awesome Free 6.4.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license (Commercial License) Copyright 2023 Fonticons, Inc. --><path d="M416 0C400 0 288 32 288 176V288c0 35.3 28.7 64 64 64h32V480c0 17.7 14.3 32 32 32s32-14.3 32-32V352 240 32c0-17.7-14.3-32-32-32zM64 16C64 7.8 57.9 1 49.7 .1S34.2 4.6 32.4 12.5L2.1 148.8C.7 155.1 0 161.5 0 167.9c0 45.9 35.1 83.6 80 87.7V480c0 17.7 14.3 32 32 32s32-14.3 32-32V255.6c44.9-4.1 80-41.8 80-87.7c0-6.4-.7-12.8-2.1-19.1L191.6 12.5c-1.8-8-9.3-13.3-17.4-12.4S160 7.8 160 16V150.2c0 5.4-4.4 9.8-9.8 9.8c-5.1 0-9.3-3.9-9.8-9L127.9 14.6C127.2 6.3 120.3 0 112 0s-15.2 6.3-15.9 14.6L83.7 151c-.5 5.1-4.7 9-9.8 9c-5.4 0-9.8-4.4-9.8-9.8V16zm48.3 152l-.3 0-.3 0 .3-.7 .3 .7z"/></svg>'
    print = '<svg xmlns="http://www.w3.org/2000/svg" height="1em" viewBox="0 0 512 512"><!--! Font Awesome Free 6.4.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license (Commercial License) Copyright 2023 Fonticons, Inc. --><path d="M128 0C92.7 0 64 28.7 64 64v96h64V64H354.7L384 93.3V160h64V93.3c0-17-6.7-33.3-18.7-45.3L400 18.7C388 6.7 371.7 0 354.7 0H128zM384 352v32 64H128V384 368 352H384zm64 32h32c17.7 0 32-14.3 32-32V256c0-35.3-28.7-64-64-64H64c-35.3 0-64 28.7-64 64v96c0 17.7 14.3 32 32 32H64v64c0 35.3 28.7 64 64 64H384c35.3 0 64-28.7 64-64V384zM432 248a24 24 0 1 1 0 48 24 24 0 1 1 0-48z"/></svg>'
    message = '<svg xmlns="http://www.w3.org/2000/svg" height="1em" viewBox="0 0 512 512"><!--! Font Awesome Free 6.4.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license (Commercial License) Copyright 2023 Fonticons, Inc. --><path d="M160 368c26.5 0 48 21.5 48 48v16l72.5-54.4c8.3-6.2 18.4-9.6 28.8-9.6H448c8.8 0 16-7.2 16-16V64c0-8.8-7.2-16-16-16H64c-8.8 0-16 7.2-16 16V352c0 8.8 7.2 16 16 16h96zm48 124l-.2 .2-5.1 3.8-17.1 12.8c-4.8 3.6-11.3 4.2-16.8 1.5s-8.8-8.2-8.8-14.3V474.7v-6.4V468v-4V416H112 64c-35.3 0-64-28.7-64-64V64C0 28.7 28.7 0 64 0H448c35.3 0 64 28.7 64 64V352c0 35.3-28.7 64-64 64H309.3L208 492z"/></svg>'
    clipboard = '<svg xmlns="http://www.w3.org/2000/svg" height="1em" viewBox="0 0 384 512"><!--! Font Awesome Free 6.4.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license (Commercial License) Copyright 2023 Fonticons, Inc. --><path d="M280 64h40c35.3 0 64 28.7 64 64V448c0 35.3-28.7 64-64 64H64c-35.3 0-64-28.7-64-64V128C0 92.7 28.7 64 64 64h40 9.6C121 27.5 153.3 0 192 0s71 27.5 78.4 64H280zM64 112c-8.8 0-16 7.2-16 16V448c0 8.8 7.2 16 16 16H320c8.8 0 16-7.2 16-16V128c0-8.8-7.2-16-16-16H304v24c0 13.3-10.7 24-24 24H192 104c-13.3 0-24-10.7-24-24V112H64zm128-8a24 24 0 1 0 0-48 24 24 0 1 0 0 48z"/></svg>'
    check = '<svg xmlns="http://www.w3.org/2000/svg" height="1em" viewBox="0 0 448 512"><!--! Font Awesome Free 6.4.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license (Commercial License) Copyright 2023 Fonticons, Inc. --><path d="M438.6 105.4c12.5 12.5 12.5 32.8 0 45.3l-256 256c-12.5 12.5-32.8 12.5-45.3 0l-128-128c-12.5-12.5-12.5-32.8 0-45.3s32.8-12.5 45.3 0L160 338.7 393.4 105.4c12.5-12.5 32.8-12.5 45.3 0z"/></svg>'
    magnifying_glass = '<svg xmlns="http://www.w3.org/2000/svg" height="1em" viewBox="0 0 512 512"><!--! Font Awesome Free 6.4.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license (Commercial License) Copyright 2023 Fonticons, Inc. --><path d="M416 208c0 45.9-14.9 88.3-40 122.7L502.6 457.4c12.5 12.5 12.5 32.8 0 45.3s-32.8 12.5-45.3 0L330.7 376c-34.4 25.2-76.8 40-122.7 40C93.1 416 0 322.9 0 208S93.1 0 208 0S416 93.1 416 208zM208 352a144 144 0 1 0 0-288 144 144 0 1 0 0 288z"/></svg>'
    link = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><!--!Font Awesome Free 6.5.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2024 Fonticons, Inc.--><path d="M320 0c-17.7 0-32 14.3-32 32s14.3 32 32 32h82.7L201.4 265.4c-12.5 12.5-12.5 32.8 0 45.3s32.8 12.5 45.3 0L448 109.3V192c0 17.7 14.3 32 32 32s32-14.3 32-32V32c0-17.7-14.3-32-32-32H320zM80 32C35.8 32 0 67.8 0 112V432c0 44.2 35.8 80 80 80H400c44.2 0 80-35.8 80-80V320c0-17.7-14.3-32-32-32s-32 14.3-32 32V432c0 8.8-7.2 16-16 16H80c-8.8 0-16-7.2-16-16V112c0-8.8 7.2-16 16-16H192c17.7 0 32-14.3 32-32s-14.3-32-32-32H80z"/></svg>'
    bars = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512"><!--!Font Awesome Free 6.6.0 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2024 Fonticons, Inc.--><path d="M0 96C0 78.3 14.3 64 32 64l384 0c17.7 0 32 14.3 32 32s-14.3 32-32 32L32 128C14.3 128 0 113.7 0 96zM0 256c0-17.7 14.3-32 32-32l384 0c17.7 0 32 14.3 32 32s-14.3 32-32 32L32 288c-17.7 0-32-14.3-32-32zM448 416c0 17.7-14.3 32-32 32L32 448c-17.7 0-32-14.3-32-32s14.3-32 32-32l384 0c17.7 0 32 14.3 32 32z"/></svg>'
    info = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 512"><!--!Font Awesome Free 6.6.0 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2024 Fonticons, Inc.--><path d="M48 80a48 48 0 1 1 96 0A48 48 0 1 1 48 80zM0 224c0-17.7 14.3-32 32-32l64 0c17.7 0 32 14.3 32 32l0 224 32 0c17.7 0 32 14.3 32 32s-14.3 32-32 32L32 512c-17.7 0-32-14.3-32-32s14.3-32 32-32l32 0 0-192-32 0c-17.7 0-32-14.3-32-32z"/></svg>'
    github = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 496 512"><!--!Font Awesome Free 6.6.0 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2024 Fonticons, Inc.--><path d="M165.9 397.4c0 2-2.3 3.6-5.2 3.6-3.3 .3-5.6-1.3-5.6-3.6 0-2 2.3-3.6 5.2-3.6 3-.3 5.6 1.3 5.6 3.6zm-31.1-4.5c-.7 2 1.3 4.3 4.3 4.9 2.6 1 5.6 0 6.2-2s-1.3-4.3-4.3-5.2c-2.6-.7-5.5 .3-6.2 2.3zm44.2-1.7c-2.9 .7-4.9 2.6-4.6 4.9 .3 2 2.9 3.3 5.9 2.6 2.9-.7 4.9-2.6 4.6-4.6-.3-1.9-3-3.2-5.9-2.9zM244.8 8C106.1 8 0 113.3 0 252c0 110.9 69.8 205.8 169.5 239.2 12.8 2.3 17.3-5.6 17.3-12.1 0-6.2-.3-40.4-.3-61.4 0 0-70 15-84.7-29.8 0 0-11.4-29.1-27.8-36.6 0 0-22.9-15.7 1.6-15.4 0 0 24.9 2 38.6 25.8 21.9 38.6 58.6 27.5 72.9 20.9 2.3-16 8.8-27.1 16-33.7-55.9-6.2-112.3-14.3-112.3-110.5 0-27.5 7.6-41.3 23.6-58.9-2.6-6.5-11.1-33.3 2.6-67.9 20.9-6.5 69 27 69 27 20-5.6 41.5-8.5 62.8-8.5s42.8 2.9 62.8 8.5c0 0 48.1-33.6 69-27 13.7 34.7 5.2 61.4 2.6 67.9 16 17.7 25.8 31.5 25.8 58.9 0 96.5-58.9 104.2-114.8 110.5 9.2 7.9 17 22.9 17 46.4 0 33.7-.3 75.4-.3 83.6 0 6.5 4.6 14.4 17.3 12.1C428.2 457.8 496 362.9 496 252 496 113.3 383.5 8 244.8 8zM97.2 352.9c-1.3 1-1 3.3 .7 5.2 1.6 1.6 3.9 2.3 5.2 1 1.3-1 1-3.3-.7-5.2-1.6-1.6-3.9-2.3-5.2-1zm-10.8-8.1c-.7 1.3 .3 2.9 2.3 3.9 1.6 1 3.6 .7 4.3-.7 .7-1.3-.3-2.9-2.3-3.9-2-.6-3.6-.3-4.3 .7zm32.4 35.6c-1.6 1.3-1 4.3 1.3 6.2 2.3 2.3 5.2 2.6 6.5 1 1.3-1.3 .7-4.3-1.3-6.2-2.2-2.3-5.2-2.6-6.5-1zm-11.4-14.7c-1.6 1-1.6 3.6 0 5.9 1.6 2.3 4.3 3.3 5.6 2.3 1.6-1.3 1.6-3.9 0-6.2-1.4-2.3-4-3.3-5.6-2z"/></svg>'


# Units
def is_weight(unit: str) -> bool:
    """Returns True if unit is a single or plural weight unit."""

    weights_df = _units[_units['type'] == 'weight']
    single_weights = set(weights_df['unit'])
    plural_weights = set(weights_df['plural'])
    weights = single_weights.union(plural_weights)
    return unit in weights


def is_volume(unit: str) -> bool:
    """Returns True if unit is a single or plural volume unit."""

    volume_df = _units[_units['type'] == 'volume']
    single_weights = set(volume_df['unit'])
    plural_weights = set(volume_df['plural'])
    volumes = single_weights.union(plural_weights)
    return unit in volumes


def is_equivalent(unit1: str, unit2: str) -> bool:
    """Determines if two units are the same.
    
    Units can be same by 3 ways:
    - unit1 and unit2 are same string
    - unit2 is plural of unit1
    - unit1 is plural of unit2
    """

    unit1 = unit1.lower()
    unit2 = unit2.lower()

    if unit1 == unit2:
        return True

    found1 = _units[(_units['unit'] == unit1) & (_units['plural'] == unit2)]
    found2 = _units[(_units['unit'] == unit2) & (_units['plural'] == unit1)]
    if found1.empty and found2.empty:
        return False
    else:
        return True


def to_standard(unit: str):
    """Returns a unit's conversion to standard."""

    unit_mask = _units['unit'] == unit
    plural_mask = _units['plural'] == unit
    standard_mask = _units['to_standard'] != 0
    matching_items = _units[(unit_mask | plural_mask) & standard_mask]
    if matching_items.empty:
        return 1
    matching_item = matching_items.iloc[0]
    return matching_item['to_standard']


def numberize(unit: str, number: (int | float)) -> str:
    """Returns single or plural unit based on number."""

    return _plural(unit) if number > 1 else _single(unit)


def _plural(unit: str) -> str:
    """Returns plural version of a unit.
    
    If unit not found, return original unit.
    """

    matching_items = _units[_units['unit'] == unit]
    if matching_items.empty:
        return unit
    matching_item = matching_items.iloc[0]    
    return matching_item['plural']


def _single(unit: str) -> str:
    """Returns singular version of a unit.
    
    If unit not found, return original unit.
    """

    matching_items = _units[_units['plural'] == unit]
    if matching_items.empty:
        return unit
    matching_item = matching_items.iloc[0]    
    return matching_item['unit']


def _load_units() -> list:
    """Loads list of units from file."""

    path = os.path.join(data_directory, 'units.csv')
    df = pd.read_csv(path)
    column_defaults = {
        'units': '',
        'plural': '',
        'type': '',
        'to_standard': 0
    }
    df.fillna(value=column_defaults, inplace=True)
    return df    


_units = _load_units()


# Fractions
unicode_fractions = {
    '1/4': '¼', 
    '1/2': '½', 
    '3/4': '¾', 
    '1/7': '⅐',
    '1/9': '⅑', 
    '1/10': '⅒', 
    '1/3': '⅓', 
    '2/3': '⅔', 
    '1/5': '⅕', 
    '2/5': '⅖', 
    '3/5': '⅗', 
    '4/5': '⅘', 
    '1/6': '⅙', 
    '5/6': '⅚', 
    '1/8': '⅛', 
    '3/8': '⅜', 
    '5/8': '⅝', 
    '7/8': '⅞'
}


def to_fraction(number: (int | float | str)) -> Fraction:
    """Converts number to Fraction.

    Args:
        number: Number or number-like string. String can include mixed numbers and unicode fractions.

    Returns:
        Number as a Fraction object.
    """

    if isinstance(number, (int, float)):
        return Fraction(number)

    # replace "1½" with "1 1/2"
    for ascii, unicode in unicode_fractions.items():
        number = number.replace(unicode, ' ' + ascii)

    amount = Fraction()
    for word in number.split():
        amount += Fraction(word)

    return amount


def fraction_to_string(my_fraction: Fraction) -> str:
    """Converts Fraction to a nice string."""

    int = floor(my_fraction)
    (num, den) = (my_fraction - int).as_integer_ratio()

    amount_parts = []
    if int:
        amount_parts.append(str(int))
    if num:
        amount_parts.append(f'{num}/{den}')

    amount_display = ' '.join(amount_parts)

    for fraction_ascii, fraction_unicode in unicode_fractions.items():
        # remove space if mixed number
        amount_display = amount_display.replace(' ' + fraction_ascii, 
                                                fraction_unicode)
        # replaces if no leading integer
        amount_display = amount_display.replace(fraction_ascii, 
                                                fraction_unicode)
    return amount_display


def format_currency(cost: (int | float)) -> str:
    """Formats a cost value as a currency string.

    This function converts a numeric cost value into a string formatted as currency. 
    The cost is rounded to two decimal places and prefixed with a dollar sign.
    """
    
    return '${:.2f}'.format(float(cost))


# URLs
def make_url(scheme=None, domain=None, path=None, params=None, query=None, fragment=None) -> str:
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
        scheme = 'https'
    if domain is None:
        domain = config('site', 'domain')
    if path is None:
        path = ''
    if params is None:
        params = ''
    if fragment is None:
        fragment = ''
    if query is None:
        query = ''
    else:
        query = urlencode(query)
    return urlunparse([scheme, domain, path, params, query, fragment])


def feedback_url(page_name: str, source_url: str) -> str:
    """Create feedback url with prefilled values."""

    components = urlparse(config('feedback', 'url'))
    query = {
        'prefill_page': page_name,
        'prefill_source_url': source_url
    }
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
    slug = slug.replace(' ', '-')
    slug = slug.replace('_', '-')

    valid = 'abcdefghijklmnopqrstuvwxyz0123456789-'
    for c in slug:
        if c not in valid:
            slug = slug.replace(c, '')

    while '--' in slug:
        slug = slug.replace('--', '-')

    return name


# Pipe
def pipe(data: dict, log_path: str, *funcs) -> dict:
    """Pipe data through a sequence of functions.

    Optionally saves data after each function in log files. Saves 
    no log if log_path is  empty string.
    """

    has_log = log_path != ''

    if has_log:
        create_dir(log_path)
        log_file_path = os.path.join(log_path, '0_start.json')
        write_json_file(data, log_file_path)

    for i, func in enumerate(funcs, 1):
        data = func(data)
        if has_log:
            log_file_path = os.path.join(log_path, f'{i}_{func.__name__}.json')
            write_json_file(data, log_file_path)

    return data




# Groceries

def grocery_info(ingredient_name):
    search_name = ingredient_name.lower()
    matching_items = _groceries[_groceries.name==search_name]

    if matching_items.empty:
        return None
    
    matching_item = matching_items.iloc[0]
    grocery_dict = matching_item.to_dict()

    return grocery_dict


def _load_groceries():
    groceries_path = os.path.join(data_directory, 'groceries.xlsx')
    groceries = pd.read_excel(groceries_path)
    column_defaults = {
        'name': '',
        'category': '',
        'url': '',
        'cost': 0,
        'volume_amount': 0,
        'volume_unit': '',
        'weight_amount': 0,
        'weight_unit': '',
        'other_amount': 0,
        'other_unit': '',
        'discrete_amount': 0,
        'calories': 0,
        'fat': 0,
        'carbohydrates': 0,
        'protein': 0,
        'tags': '',
        'notes': ''
    }
    groceries.fillna(value=column_defaults, inplace=True)
    return groceries


_groceries = _load_groceries()


# Qr codes
def make_qr_file(link: str, filepath: str) -> None:
    qr_code = make_qr(link)
    qr_code.save(filepath, scale=5, border=0)
