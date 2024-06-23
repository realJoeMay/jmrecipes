import os
import datetime
import shutil
import json
from collections import defaultdict

from parser import parse_recipe
from utils import builds_directory, data_directory, assets_directory, create_dir, make_empty_dir, write_file, render_template
from utils import site_title, feedback_url, icon, fraction_to_string, make_url, to_fraction, make_qr_file, pipe, sluggify
from utils import numberize_unit


def build():
    """Execute a build of the recipe site.
    
    Loads site data and creates a recipe website. Also creates a local version of site.
    """

    ts = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')

    latest = os.path.join(builds_directory, 'latest')
    site_web = os.path.join(latest, 'web')
    site_local = os.path.join(latest, 'local')
    log = os.path.join(latest, 'build-log')

    create_dir(builds_directory)
    make_empty_dir(latest)
    create_dir(log)

    site = load_site(data_directory, log)
    build_site(site, site_web)
    build_site(site, site_local, local=True)

    stamp = os.path.join(builds_directory, ts)
    shutil.copytree(latest, stamp)


def load_site(data_path: str, log_path: str) -> dict:
    """Loads site data from directory.
    
    Args:
        data_path: Directory with site data files.
        log: Directory to save log files.

    Returns:
        Site data as a dictionary.
        {'recipes': [r1, r2, r3],
         'collection': [c1, c2]}
    """

    recipes_path = os.path.join(data_path, 'recipes')
    collections_path = os.path.join(data_path, 'collections')
    site = {
        'recipes': load_recipes(recipes_path, log_path),
        'collections': load_collections(collections_path, log_path)
    }
    return pipe(site,
                log_path,
                link_recipes_collections
                )


def load_recipes(recipes_path: str, log_path: str) -> list:
    """Loads data for recipes.
    
    Args:
        recipes_path: Directory that contains recipe data folders.
        log: Directory to save log files.

    Returns:
        Recipes data as a list of dictionaries, one for each recipe.
    """

    recipes_log_path = os.path.join(log_path, 'recipes')
    create_dir(recipes_log_path)
    recipes = []
    for folder in os.listdir(recipes_path):
        recipe_path = os.path.join(recipes_path, folder)
        recipe_log_path = os.path.join(recipes_log_path, folder)
        create_dir(recipe_log_path)
        recipes.append(load_recipe(recipe_path, recipes_log_path))
    return recipes


def load_recipe(recipe_path: str, log_path=None) -> dict:
    """Generates recipe data from a folder.

    Extracts data from folder, including the data file, image, and folder name 
    as url_slug. Then, process the data to include everything needed for site.
    
    Args:
        recipe_path: Directory for a recipe's data.
        log_path: Directory to save log files.

    Returns:
        Recipes data as a dictionary.
    """

    file = recipe_file(recipe_path)
    filepath = os.path.join(recipe_path, file)

    recipe = parse_recipe(filepath)
    folder = os.path.basename(recipe_path)
    recipe['url_slug'] = sluggify(folder)

    recipe['has_image'] = False
    image = recipe_image(recipe_path)
    if image:
        recipe['has_image'] = True
        recipe['image'] = image
        recipe['image_src_path'] = os.path.join(recipe_path, image)

    if log_path is None:
        log_path = ''
    else:
        log_path = os.path.join(log_path, recipe['url_slug'])

    return pipe(recipe, 
                log_path,
                set_url,
                set_title,
                set_image,
                set_scales,
                set_yields,
                set_ingredients,
                set_instructions,
                set_has_description_area,
                set_schema
                )


def set_url(recipe):
    """Sets values regarding the URLs."""

    recipe['url_path'] = '/' + recipe['url_slug']
    recipe['url'] = make_url(path=recipe['url_path'])
    recipe['feedback_url'] = feedback_url(recipe['title'], recipe['url'])
    return recipe


def set_title(recipe: dict) -> dict:
    """Sets values regarding the recipe title and subtitle."""
    
    if 'subtitle' in recipe and recipe['subtitle'] != '':
        recipe['has_subtitle'] = True
        recipe['subtitle'] = recipe['subtitle'].lower()
    else:
        recipe['has_subtitle'] = False

    return recipe

    

def set_image(recipe: dict) -> dict:
    """Sets recipe data regarding the image."""

    if recipe['has_image']:
        recipe['image_url'] = '/'.join((recipe['url_slug'], recipe['image']))
    else:
        recipe['image_url'] = 'default.jpg'
    return recipe


def set_scales(recipe: dict) -> dict:
    """Sets recipe data regarding the recipe scales."""

    for i, scale in enumerate(recipe['scales'], 1):
        label = str(scale['multiplier'].limit_denominator(100)) + 'x'
        scale['label'] = label
        scale['item_class'] = f'scale-{label}'
        scale['select_class'] = f'display-scale-{label}'
        scale['button_class'] = f'display-scale-{label}-btn'
        scale['js_function_name'] = f'scale{label}'
        scale['keyboard_shortcut'] = i
    recipe['base_select_class'] = recipe['scales'][0]['select_class']
    recipe['has_scales'] = len(recipe['scales']) > 1
    return recipe


def copy_ingredients_sublabel(scale):

    if scale['multiplier'] == 1:
        return ''
    
    if scale['has_servings']:
        unit = 'serving' if scale['servings'] ==1 else 'servings'
        return f'for {scale["servings"]} {unit}'
    
    return f'for {scale["multiplier"]}x'


def set_yields(recipe: dict) -> dict:
    """Set recipe attributes related to yield."""

    # set defaults
    for yielb in recipe['yield']:
        if yielb['show_yield'] == '':
            yielb['show_yield'] = True
        if yielb['show_serving_size'] == '':
            yielb['show_serving_size'] = False

    # todo make nicer
    for scale in recipe['scales']:
        scale = scale_yields(scale, recipe['yield'])
        scale = set_yield_displays(scale)
        scale = set_servings(scale)
        scale = set_serving_size(scale)
        scale['copy_ingredients_sublabel'] = copy_ingredients_sublabel(scale)

    return recipe


def scale_yields(scale, base_yields):
    """Add yield data to recipe scales."""

    scale['yield'] = []
    for yielb in base_yields:
        number = yielb['number'] * scale['multiplier']
        scale['yield'].append({
            'number': number,
            'unit': numberize_unit(yielb['unit'], number),
            'show_yield': yielb['show_yield'],
            'show_serving_size': yielb['show_serving_size']
        })
    return scale


def set_yield_displays(scale):

    scale['has_visible_yields'] = False
    for yielb in scale['yield']:
        if yielb['show_yield']:
            scale['has_visible_yields'] = True
            yielb['yield_string'] = yield_display(yielb)

    return scale


def yield_display(yielb: dict) -> str:
    """Returns string for a yield."""

    number = fraction_to_string(yielb["number"])
    display = f'{number} {yielb["unit"]}'
    return display


def set_servings(scale):
    """Sets recipe scale servings data."""

    scale['has_servings'] = False
    for yielb in scale['yield']:
        if yielb['unit'].lower() in ('serving', 'servings'):
            scale['servings'] = yielb['number']
            scale['has_servings'] = True
            
            number = fraction_to_string(yielb['number'])
            unit = 'serving' if number == 1 else 'servings'
            scale['servings_string'] = f'{number} {unit}'
            
    return scale


def set_serving_size(scale):
    """Sets recipe scale servings size data."""

    scale['has_visible_serving_sizes'] = False

    if scale['has_servings'] is False:
        return scale
    
    for yielb in scale['yield']:
        if yielb['show_serving_size']:
            scale['has_visible_serving_sizes'] = True
            number = yielb['number'] / scale['servings']
            number_string = fraction_to_string(number)
            unit = numberize_unit(yielb['unit'], number)
            yielb['serving_size_string'] = f'{number_string} {unit}'

    return scale


def set_instructions(recipe):
    """Sets recipe data regarding instructions."""

    for scale in recipe['scales']:
        scale['instructions'] = []
        for step in recipe['instructions']:
            if 'scale' not in step or to_fraction(step['scale']) == scale['multiplier']:
                scale['instructions'].append(step.copy())
        scale['has_instructions'] = bool(scale['instructions'])

    recipe = set_instruction_lists(recipe)
    recipe = number_steps(recipe)
    return recipe


def number_steps(recipe):
    """Sets step numbers for instructions."""

    for scale in recipe['scales']:
        for steps in scale['instruction_lists'].values():
            for i, step in enumerate(steps, 1):
                step['number'] = i
    return recipe


def set_ingredients(recipe: dict) -> dict:
    """Sets recipe data regarding ingredients."""

    for ingredient in recipe['ingredients']:
        ingredient = set_ingredient_displays(ingredient)

    for scale in recipe['scales']:
        scale['ingredients'] = scale_ingredients(recipe['ingredients'], 
                                                 scale['multiplier'])
        scale['has_ingredients'] = bool(scale['ingredients'])

        for ingredient in scale['ingredients']:
            ingredient['string'] = ingredient_string(ingredient)
            ingredient['display_amount'] = ingredient_display_amount(ingredient)
    
    recipe = set_ingredient_lists(recipe)

    return recipe


def ingredient_display_amount(ing):
    """Return string with ingredient number and unit."""

    display_amount = []
    if ing['display_number']:
        display_amount.append(fraction_to_string(ing['display_number']))
    if ing['display_unit']:
        display_amount.append((ing['display_unit']))
    amount = ' '.join(display_amount)
    
    return amount


def ingredient_string(ing):

    i_str = []
    if ing['display_number']:
        i_str.append(fraction_to_string(ing['display_number']))
    if ing['display_unit']:
        i_str.append((ing['display_unit']))
    if ing['display_item']:
        i_str.append((ing['display_item']))
    string = ' '.join(i_str)
    return string


def set_ingredient_displays(ing: dict) -> dict:
    """Fill missing ingredient display data."""

    if ing['display_number'] == 0:
        ing['display_number'] = ing['number']

    if ing['display_unit'] == '':
        ing['display_unit'] = ing['unit']

    if ing['display_item'] == '':
        ing['display_item'] = ing['item']

    return ing


def scale_ingredients(base_ingredients, multiplier) -> dict:
    """Get list of ingredients for a recipe scale.

    Base ingredients are scaled using a multiplier. If the base ingredient has 
    an explicit scale, the ingredient is copied without multiplying.

    Args:
        base_ingredients: Ingredient data as a directory.
        multiplier: A scale's multiplier as a fraction.

    Returns:
        List of ingredient dictionaries.
    """

    ingredients = []
    for ingredient in base_ingredients:
        if 'scale' not in ingredient:
            ingredients.append(scale_ingredient(ingredient, multiplier))
        elif to_fraction(ingredient['scale']) == multiplier:        
            ingredients.append(ingredient)

    return ingredients


def scale_ingredient(ingredient, multiplier):
    """"""

    scaled = ingredient.copy()
    scaled['number'] = ingredient['number'] * multiplier
    scaled['display_number'] = ingredient['display_number'] * multiplier
    return scaled



def set_ingredient_lists(recipe):
    """Groups ingredients into ingredient lists."""
    
    for scale in recipe['scales']:
        scale['ingredient_lists'] = defaultdict(list)
        for ingredient in scale['ingredients']:
            scale['ingredient_lists'][ingredient.get('list', 'Ingredients')].append(ingredient)

    return recipe


def set_instruction_lists(recipe):
    """Groups instruction steps into step lists."""
    
    for scale in recipe['scales']:
        scale['instruction_lists'] = defaultdict(list)
        for step in scale['instructions']:
            scale['instruction_lists'][step.get('list', 'Instructions')].append(step)

    return recipe


def set_has_description_area(recipe: dict) -> dict:
    """Sets recipe data regarding the description area."""

    for scale in recipe['scales']:
        scale['has_description_area'] = False

        if scale['has_visible_yields']:
            scale['has_description_area'] = True


    return recipe


def set_schema(recipe: dict) -> dict:
    """Add schema to recipe data.

    More about recipe schema. 
    https://schema.org/Recipe

    Args:
        recipe: Recipe data as a directory.

    Returns:
        Recipe data as a dictionary.
    """

    schema = {
        '@context': 'https://schema.org',
        '@type': 'Recipe',
        'name': recipe['title']
    }

    if recipe['has_image']:
        schema['image'] = recipe['image']

    if recipe['scales'][0]['has_servings']:
        schema['recipeYield'] = recipe['scales'][0]['servings_string']

    if recipe['scales'][0]['has_ingredients']:
        schema['recipeIngredient'] = []
        for ingredient in recipe['scales'][0]['ingredients']:
            schema['recipeIngredient'].append(ingredient['string'])

    recipe['schema_string'] = json.dumps(schema)
    return recipe


def recipe_file(recipe_path: str) -> str:
    """Finds a recipe data file inside a folder.
    
    Args:
        recipe_path: A directory to search in.

    Returns:
        Filename of the recipe data file as a string.

    Raises:
        OSError: If no recipe data file was found.
    """
    
    for file in os.listdir(recipe_path):
        if file.endswith('.json'):
            return file
        elif file.endswith('.yaml'):
            return file
    raise OSError(f'Data file not found in {dir}')


def recipe_image(recipe_path):
    """Finds a recipe image file inside a folder.
    
    Args:
        recipe_path: A directory to search in.

    Returns:
        Filename of the recipe data file as a string, or empty string if no 
        image found.
    """
    
    for file in os.listdir(recipe_path):
        if file.endswith(('.jpg', '.jpeg', 'png')):
            return file
    return ''


def load_collections(collections_path: str, log_path: str) -> list:
    """Generates data for collections.
    
    Args:
        collections_path: Directory that contains collections data files.
        log_path: Directory to save log files.

    Returns:
        Collections data as a list of dictionaries.
    """

    c_log_path = os.path.join(log_path, 'collections')
    create_dir(c_log_path)
    collections = []
    for file in os.listdir(collections_path):
        file_path = os.path.join(collections_path, file)    
        collections.append(load_collection(file_path, c_log_path))
    return collections


def load_collection(file_path: str, log_path: str) -> dict:
    """Generates data for a collection.
    
    Args:
        file_path: Directory that contains collections data files.
        log_path: Directory to save log files.

    Returns:
        Collection data as a dictionary.
    """

    with open(file_path, 'r', encoding='utf8') as f:
        data = json.load(f)

    return pipe(data,
                os.path.join(log_path, data['name']),
                set_homepage,
                set_href
                )


def set_homepage(collection):
    
    collection['is_homepage'] = False
    if collection['url_path'] == '':
        collection['is_homepage'] = True
    
    return collection


def set_href(collection):
    """Set href to a collectvion from a recipe page."""

    if collection['is_homepage']:
        collection['href'] = '..'
    else:
        collection['href'] = f'../{collection["url_path"]}'

    return collection


def link_recipes_collections(site: dict) -> dict:
    """Adds collections data to recipes and vice versa.
    
    Args:
        site: Site data with recipes and collections.

    Returns:
        Updated site data as a dictionary.
    """

    recipes = site['recipes']
    for r in recipes:
        r['collections'] = []

    for c in site['collections']:
        for i, url_slug in enumerate(c['recipes']):
            for r in recipes:
                if r['url_slug'] == url_slug:
                    r['collections'].append(info_for_recipe(c))
                    c['recipes'][i] = info_for_collection(r)

    return site


def info_for_collection(recipe: dict) -> dict:
    """Recipe data needed for collection page.

    Args:
        recipe: Recipe data as a dictionary.

    Returns:
        Stripped down recipe data as a dictionary.
    """

    keys = ('title', 'url_slug', 'subtitle', 'has_subtitle', 'image_url')
    return {k: recipe[k] for k in keys if k in recipe}


def info_for_recipe(collection: dict) -> dict:
    """Collection data needed for recipe page.

    Args:
        collection: Collection data as a dictionary.

    Returns:
        Stripped down collection data as a dictionary.
    """

    keys = ('name', 'url_path', 'label', 'href')
    return {k: collection[k] for k in keys if k in collection}


def build_site(site: dict, site_path: str, local=False):
    """Builds a recipe site from site data.

    Args:
        site: Site data as a dictionary.
        site_path: Path to build the site inside.
        local: Builds local version if true. Builds web version otherwise. Defaults is False.
    """
    
    make_empty_dir(site_path)

    for recipe in site['recipes']:
        recipe_dir = os.path.join(site_path, recipe['url_slug'])
        make_recipe_page(recipe, recipe_dir, local)
        make_qr_file(recipe['url'], os.path.join(recipe_dir, 'recipe-qr.png'))
        make_print_page(recipe, os.path.join(recipe_dir, 'p'), local)
        if recipe['has_image']:
            shutil.copyfile(
                recipe['image_src_path'],
                os.path.join(recipe_dir, recipe['image']))

    for collection in site['collections']:
        collection_dir = get_collection_dir(collection, site_path)
        make_collection_page(collection, collection_dir, local)

    make_summary_page(site, os.path.join(site_path, 'summary.html'))

    shutil.copyfile(
        os.path.join(assets_directory, 'icon.png'), 
        os.path.join(site_path, 'icon.png'))
    shutil.copyfile(
        os.path.join(assets_directory, 'default_720x540.jpg'), 
        os.path.join(site_path, 'default.jpg'))


def get_collection_dir(collection, site_path):

    if collection['is_homepage']:
        return site_path
    
    return os.path.join(site_path, collection['url_path'])


def make_recipe_page(recipe: dict, dir: str, local: bool):
    """Create index.html file for recipe page.

    Args:
        recipe: Recipe data as a dictionary.
        dir: Path to build the page inside.
        local: Builds local version if true. Builds web version otherwise.
    """

    create_dir(dir)
    file = os.path.join(dir, 'index.html')
    content = render_template('recipe-page.html', 
                              r=recipe, 
                              icon=icon,
                              site_title=site_title(),
                              is_local=local)
    write_file(content, file)


def make_print_page(recipe: dict, dir: str, local: bool):
    """Create index.html file for recipe print page.

    Args:
        recipe: Recipe data as a dictionary.
        dir: Path to build the page inside.
        local: Builds local version if true. Builds web version otherwise.
    """

    create_dir(dir)
    file = os.path.join(dir, 'index.html')
    content = render_template('print-page.html', 
                              r=recipe, 
                              is_local=local,
                              site_title=site_title(),
                              icon=icon
                              )
    write_file(content, file)


def make_collection_page(collection: dict, dir: str, local: bool):
    """Create index.html file for collection page.

    Args:
        collection: Collection data as a dictionary.
        dir: Path to build the page inside.
        local: Builds local version if true. Builds web version otherwise.
    """

    create_dir(dir)
    file = os.path.join(dir, 'index.html')
    content = render_template('collection.html', 
                              c=collection,
                              is_local=local,
                              site_title=site_title(),
                              icon=icon
                              )
    write_file(content, file)


def make_summary_page(site: dict, page_path: str):
    """Create summary page for recipe site.

    Args:
        site: Site data as a dictionary.
        page_path: File path for summary page.
    """

    content = render_template('summary-page.html', 
                              recipes=site['recipes'], 
                              collections=site['collections'],
                              site_title=site_title()
                              )
    write_file(content, page_path)


if __name__ == "__main__":
    build()