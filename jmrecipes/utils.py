import os
from configparser import ConfigParser
from jinja2 import Environment, FileSystemLoader
import shutil
from json import JSONEncoder
import json
from fractions import Fraction
from math import floor
from urllib.parse import urlparse, urlunparse, urlencode
from segno import make_qr
import os
import pandas as pd


# Directories
file_directory = os.path.dirname(os.path.abspath(__file__))
project_directory = os.path.split(file_directory)[0]
builds_directory = os.path.join(project_directory, 'builds')
data_directory = os.path.join(project_directory, 'data')
jmr_directory = file_directory
assets_directory = os.path.join(jmr_directory, 'assets')
templates_directory = os.path.join(jmr_directory, 'templates')


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

def config(section: str, name: str) -> str:
    """Read information from config file."""

    config_path = os.path.join(data_directory, 'config.ini')
    parser = ConfigParser()
    parser.read(config_path)
    return parser.get(section, name)


def site_title() -> str:
    """Read site title from config file."""

    return config('site', 'title')


def site_domain() -> str:
    """Read site domain from config file."""

    return config('site', 'domain')


def config_feedback_url() -> str:
    """Read feedback url from config file."""

    return config('feedback', 'url')


# Templates

def render_template(template_name: str, **context):
    file_directory = os.path.dirname(os.path.abspath(__file__))
    templates_path = os.path.join(file_directory, 'templates')
    environment = Environment(loader=FileSystemLoader(templates_path))
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


# Units
def is_weight(unit: str) -> bool:
    """Returns True if unit is a weight unit, single or plural."""

    weights_df = _units[_units['type'] == 'weight']
    single_weights = set(weights_df['unit'])
    plural_weights = set(weights_df['plural'])
    weights = single_weights.union(plural_weights)
    return unit in weights


def is_volume(unit: str) -> bool:
    """Returns True if unit is a volume unit, single or plural."""

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


def to_standard(unit):
    """Returns a unit's conversion to standard."""

    unit_mask = _units['unit'] == unit
    plural_mask = _units['plural'] == unit
    standard_mask = _units['to_standard'] != 0
    matching_items = _units[(unit_mask | plural_mask) & standard_mask]
    if matching_items.empty:
        return 1
    matching_item = matching_items.iloc[0]
    return matching_item['to_standard']


def numberize(unit: str, number) -> str:
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

# todo get this working
# i need to add mulitply and divide to keep in ffraction
# also replace to_fraction with init, 
# class FFraction(Fraction):
#     def __str__(self):
#         """Converts Fraction to a nice string."""

#         int = floor(self)
#         (num, den) = (self - int).as_integer_ratio()

#         amount_parts = []
#         if int:
#             amount_parts.append(str(int))
#         if num:
#             amount_parts.append(f'{num}/{den}')

#         amount_display = ' '.join(amount_parts)

#         for fraction_ascii, fraction_unicode in unicode_fractions.items():
#             # remove space if mixed number
#             amount_display = amount_display.replace(' ' + fraction_ascii, 
#                                                     fraction_unicode)
#             # replaces if no leading integer
#             amount_display = amount_display.replace(fraction_ascii, 
#                                                     fraction_unicode)
#         return amount_display


def to_fraction(number) -> Fraction:
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


# URLs
def make_url(scheme=None, domain=None, path=None, params=None, query=None, fragment=None):
    """Makes a url from components."""

    if scheme is None:
        scheme = 'https'
    if domain is None:
        domain = site_domain()
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
    

    components = urlparse(config_feedback_url())
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

    Args:
        name: String to convert to slug

    Returns:
        URL slug as a string.
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

    Optionally saves data after each function in log files.

    Args:
        data: Data as a dictionary.
        log_path: Directory to hold the pipe's log files. Saves no log if empty string.
        *funcs: Functions that will be called on the data.

    Returns:
        Data after applying functions as a dictionary.
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
        'Calories': 0,
        'fat': 0,
        'carbohydrates': 0,
        'protein': 0,
        'notes': ''
    }
    groceries.fillna(value=column_defaults, inplace=True)
    return groceries


_groceries = _load_groceries()


# Qr codes
def make_qr_file(link, filepath):
    qr_code = make_qr(link)
    qr_code.save(filepath, scale=5, border=0)
