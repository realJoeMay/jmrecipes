import os
import datetime
import shutil
import json
import math
from collections import defaultdict
from urllib.parse import urlparse

import sys
file_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.split(file_dir)[0]
sys.path.append(project_dir)

from src.parser import parse_recipe
import src.utils as utils


def build():
    """Loads site data and creates a recipe website."""

    ts = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')

    latest = os.path.join(utils.builds_directory, 'latest')
    site_web = os.path.join(latest, 'web')
    site_local = os.path.join(latest, 'local')
    log = os.path.join(latest, 'build-log')

    utils.create_dir(utils.builds_directory)
    utils.make_empty_dir(latest)
    utils.create_dir(log)

    site = load_site(utils.data_directory, log)
    build_site(site, site_web, verbose=True)
    build_site(site, site_local, local=True)

    stamp = os.path.join(utils.builds_directory, ts)
    shutil.copytree(latest, stamp)
    print('Build complete')


def load_site(data_path, log_path=None) -> dict:
    """Loads site data from directory.
    
    Args:
        data_path: Directory with site data files.
        log: Directory to save site level log files.

    Returns:
        Site data as a dictionary.
        {'recipes': [r1, r2, r3],
         'collection': [c1, c2]}
    """

    recipes_path = os.path.join(data_path, 'recipes')
    collections_path = os.path.join(data_path, 'collections')
    has_log = log_path is not None

    if has_log:
        recipes_log_path = os.path.join(log_path, 'recipes')
        collections_log_path = os.path.join(log_path, 'collections')
        recipes = load_recipes(recipes_path, log_path=recipes_log_path)
        collections = load_collections(collections_path, log_path=collections_log_path)
        pipe_log_path = log_path
    else:
        recipes = load_recipes(recipes_path)
        collections = load_collections(collections_path)
        pipe_log_path = ''

    site = {
        'recipes': recipes,
        'collections': collections
    }
    return utils.pipe(site, pipe_log_path,
                      set_child_recipe_links,
                      set_recipes_used_in,
                      set_ingredient_as_recipe_quantities,
                      set_costs,
                      set_costs_per_serving,
                      set_cost_strings,
                      set_nutrition,
                      set_display_nutrition,
                      set_ingredient_details,
                      set_description_areas,
                      set_ingredient_lists,
                      link_recipes_collections,
                      set_search_values,
                      set_summary)


def load_recipes(recipes_path: str, log_path:str = None) -> list:
    """Loads data for recipes.
    
    Args:
        recipes_path: Directory that contains recipe data folders.
        log: Directory to save recipes level log files.

    Returns:
        Recipes data as a list of dictionaries, one for each recipe.
    """

    has_log = log_path is not None
    if has_log:
        utils.create_dir(log_path)

    recipes = []
    for folder in os.listdir(recipes_path):
        recipe_path = os.path.join(recipes_path, folder)
        
        if has_log:
            recipe_log_path = os.path.join(log_path, folder)
            utils.create_dir(recipe_log_path)
            recipes.append(load_recipe(recipe_path, log_path))
        else:
            recipes.append(load_recipe(recipe_path))

    return recipes


def load_recipe(recipe_path: str, log_path=None) -> dict:
    """Generates recipe data from a folder.

    Extracts data from folder, including the data file, image, and folder name 
    as url_slug. Then, process the data to include everything needed for site.
    
    Args:
        recipe_path: Directory for a recipe's data.
        log_path: Directory to save recipe pipe log files.

    Returns:
        Recipes data as a dictionary.
    """

    file = recipe_file(recipe_path)
    filepath = os.path.join(recipe_path, file)

    recipe = parse_recipe(filepath)
    folder = os.path.basename(recipe_path)
    recipe['url_slug'] = utils.sluggify(folder)

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

    return utils.pipe(recipe, log_path,
                      set_defaults,
                      set_url,
                      set_subtitle,
                      set_description,
                      set_image,
                      set_scales,
                      set_times,
                      scale_yields,
                      set_servings,
                      set_visible_yields,
                      set_visible_serving_sizes,
                      set_copy_ingredients_sublabel,
                      set_ingredients_type,
                      scale_ingredients,
                      set_ingredient_outputs,
                      lookup_groceries,
                      set_instructions,
                      set_sources,
                      set_notes,
                      set_schema,
                      set_search_targets)


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


def recipe_image(recipe_path: str) -> str:
    """Finds a recipe image file inside a folder.
    
    Args:
        recipe_path: A directory to search in.

    Returns:
        Filename of the image file as a string, or empty string if no image.
    """
    
    for file in os.listdir(recipe_path):
        if file.endswith(('.jpg', '.jpeg', 'png')):
            return file
    return ''


def set_defaults(recipe):
    """Sets default values for keys if not already set.
    
    Sets the following default values:
    - 'hide_cost': False.
    - 'hide_nutrition': False.

    Sets the following default values for each yield in recipe:
    - 'unit': 'servings'.
    - 'show_yield': True.
    - 'show_serving_size': False.
    """

    for yielb in recipe['yield']:
        if 'unit' not in yielb:
            yielb['unit'] = 'servings'
        if 'show_yield' not in yielb:
            yielb['show_yield'] = True
        if 'show_serving_size' not in yielb:
            yielb['show_serving_size'] = False

    if 'hide_cost' not in recipe:
        recipe['hide_cost'] = False
    if 'hide_nutrition' not in recipe:
        recipe['hide_nutrition'] = False

    return recipe


def set_url(recipe):
    """Sets values regarding the URLs for the given recipe.

    Sets the following keys:
    - 'url_path' (str)
    - 'url' (str)
    - 'feedback_url' (str)
    """

    recipe['url_path'] = '/' + recipe['url_slug']
    recipe['url'] = utils.make_url(path=recipe['url_path'])
    recipe['feedback_url'] = utils.feedback_url(recipe['title'], recipe['url'])
    return recipe


def set_subtitle(recipe):
    """Sets values related to the recipe's subtitle.

    Sets the following keys:
    - 'has_subtitle' (bool)
    """
    
    if 'subtitle' in recipe and recipe['subtitle'] != '':
        recipe['has_subtitle'] = True
        recipe['subtitle'] = recipe['subtitle'].lower()
    else:
        recipe['has_subtitle'] = False

    return recipe


def set_description(recipe):
    """Sets a flag indicating the presence of a recipe description.

    Sets the following keys:
    - 'has_description' (bool)
    """

    recipe['has_description'] = 'description' in recipe
    return recipe


def set_image(recipe):
    """Sets the image URL for the recipe.

    Sets the following keys:
    - 'has_image' (bool)
    - 'image_url' (str)
    """

    if recipe['has_image']:
        recipe['image_url'] = '/'.join((recipe['url_slug'], recipe['image']))
    else:
        recipe['image_url'] = 'default.jpg'
    return recipe


def set_scales(recipe):
    """Sets scale-related values for each scale.

    Sets the following keys:
    - 'base_select_class' (str)
    - 'has_scales' (bool)

    Sets the following keys for each scale:
    - 'label' (str)
    - 'item_class' (str)
    - 'select_class' (str)
    - 'button_class' (str)
    - 'js_function_name' (str)
    - 'keyboard_shortcut' (str)
    """

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


def set_times(recipe):
    """Set recipe attributes related to cook times.
    
    Sets the following keys for each scale:
    - 'times' (list)
    - 'has_times' (bool)

    Sets the following keys for each time:
    - 'unit' (str)
    - 'time_string' (str)
    """

    for time in recipe['times']:

        if 'unit' not in time or time['unit'] == '':
            time['unit'] = 'minutes' if time['time'] > 1 else 'minute'

        time_string = utils.fraction_to_string(time['time'])
        time['time_string'] = f'{time_string} {time["unit"]}'

    for scale in recipe['scales']:
        scale['times'] = recipe['times']
        scale['has_times'] = bool(scale['times'])

    return recipe


def scale_yields(recipe):
    """Add yield section to each scale.
    
    Sets the following keys for each scale:
    - 'yield' (list)
    """

    for scale in recipe['scales']:
        scale['yield'] = []
        for yielb in recipe['yield']:
            number = yielb['number'] * scale['multiplier']
            scale['yield'].append({
                'number': number,
                'unit': utils.numberize(yielb['unit'], number),
                'show_yield': yielb['show_yield'],
                'show_serving_size': yielb['show_serving_size']})
    return recipe


def set_servings(recipe):
    """Sets servings data for each scale.
    
    Sets the following keys:
    - 'has_servings' (bool)

    Sets the following keys for each scale:
    - 'has_servings' (bool)

    Sets the following keys for each scale with servings:
    - 'servings' (int)
    """

    for scale in recipe['scales']:
        scale['has_servings'] = False
        for yielb in scale['yield']:
            if yielb['unit'].lower() in ('serving', 'servings'):
                scale['servings'] = yielb['number']
                scale['has_servings'] = True



    recipe['has_servings'] = recipe['scales'][0]['has_servings']
    return recipe


def set_visible_yields(recipe):
    """Sets yield data to appear on page.

    Sets the following keys for each scale:
    - 'has_visible_yields' (bool)

    Sets the following keys for each yield:
    - 'yield_string' (str)
    """

    for scale in recipe['scales']:
        scale['has_visible_yields'] = False
        for yielb in scale['yield']:
            if yielb['show_yield']:
                scale['has_visible_yields'] = True
                yielb['yield_string'] = yield_string(yielb)

    return recipe


def yield_string(yielb: dict) -> str:
    """String represeentation of a yield."""

    number = utils.fraction_to_string(yielb["number"])
    return f'{number} {yielb["unit"]}'


def set_visible_serving_sizes(recipe):
    """Sets servings size data for each scale.
    
    Sets the following keys for each scale:
    - 'has_visible_serving_sizes' (bool)

    Sets the following keys for each yield if showing serving size:
    - 'serving_size_string' (str)
    """

    for scale in recipe['scales']:
        scale = set_serving_size(scale)
    return recipe


def set_serving_size(scale):
    """Sets servings size data for a scale."""

    scale['has_visible_serving_sizes'] = False

    if scale['has_servings'] is False:
        return scale
    
    for yielb in scale['yield']:
        if yielb['show_serving_size']:
            scale['has_visible_serving_sizes'] = True
            number = yielb['number'] / scale['servings']
            number_string = utils.fraction_to_string(number)
            unit = utils.numberize(yielb['unit'], number)
            yielb['serving_size_string'] = f'{number_string} {unit}'
    return scale


def set_copy_ingredients_sublabel(recipe):
    """Set sublabel of copy ingredients button for each scale.    
    
    Sets the following keys for each scale:
    - 'copy_ingredients_sublabel' (str)
    """

    for scale in recipe['scales']:
        scale['copy_ingredients_sublabel'] = copy_ingredients_sublabel(scale)
    return recipe


def copy_ingredients_sublabel(scale: dict) -> str:
    """Returns sublabel for copy ingredients button.
    
    The sublabel is based on the following:
    - [Empty string] if scale is base scale
    - '4 servings' if servings is set
    - '2x' otherwise
    """

    if scale['multiplier'] == 1:
        return ''
    
    if scale['has_servings']:
        unit = 'serving' if scale['servings'] ==1 else 'servings'
        return f'for {scale["servings"]} {unit}'
    
    return f'for {scale["multiplier"]}x'


def set_ingredients_type(recipe):
    """Sets the ingredient type for each ingredient.

    Sets the following keys for each ingredient:
    - 'is_recipe' (bool)
    - 'is_grocery' (bool)
    """

    for ingredient in recipe['ingredients']:
        ingredient['is_recipe'] = 'recipe_slug' in ingredient
        ingredient['is_grocery'] = not(ingredient['is_recipe'])
    return recipe


def scale_ingredients(recipe):
    """Add ingredients list to each recipe scale.
    
    Sets the following keys for each scale:
    - 'ingredients' (list)
    - 'has_ingredients' (bool)
    """

    for scale in recipe['scales']:
        scale['ingredients'] = ingredients_in_scale(recipe['ingredients'], 
                                                    scale['multiplier'])
        scale['has_ingredients'] = bool(scale['ingredients'])
    return recipe


def ingredients_in_scale(base_ingredients, multiplier) -> list:
    """Get list of ingredients for a recipe scale.

    Ingredients are scaled using a multiplier. If the base 
    ingredient has an explicit scale, the ingredient is copied without 
    multiplying.
    """

    ingredients = []
    for ingredient in base_ingredients:
        if 'scale' not in ingredient:
            ingredients.append(multiply_ingredient(ingredient, multiplier))
        elif utils.to_fraction(ingredient['scale']) == multiplier:
            ingredients.append(ingredient)
    return ingredients


def multiply_ingredient(ingredient, multiplier) -> dict:
    """Returns ingredient data scaled by multiplier."""

    scaled = ingredient.copy()
    scaled['number'] = ingredient['number'] * multiplier
    scaled['display_number'] = ingredient['display_number'] * multiplier
    if 'explicit_cost' in ingredient:
        scaled['explicit_cost'] = ingredient['explicit_cost'] * multiplier
    if 'explicit_nutrition' in ingredient:
        scaled['explicit_nutrition'] = multiply_nutrition(
            ingredient['explicit_nutrition'], multiplier)
    return scaled


def set_ingredient_outputs(recipe):
    """Sets display values for ingredients.
    
    Sets the following keys for each scaled ingredient:
    - 'string' (str)
    - 'display_amount' (str)
    """

    for ingredient in ingredients_in(recipe):
        if ingredient['display_number'] == 0:
            ingredient['display_number'] = ingredient['number']
        if ingredient['display_unit'] == '':
            ingredient['display_unit'] = ingredient['unit']
        if ingredient['display_item'] == '':
            ingredient['display_item'] = ingredient['item']
        ingredient['string'] = ingredient_string(ingredient)
        ingredient['display_amount'] = ingredient_display_amount(ingredient)
    return recipe


def ingredient_string(ing: dict) -> str:
    """String for ingredient with number, unit, and item."""

    i_str = []
    if ing['display_number']:
        i_str.append(utils.fraction_to_string(ing['display_number']))
    if ing['display_unit']:
        i_str.append((ing['display_unit']))
    if ing['display_item']:
        i_str.append((ing['display_item']))
    string = ' '.join(i_str)
    return string


def ingredient_display_amount(ingredient):
    """String for ingredient with number and unit."""

    amount = []
    if ingredient['display_number']:
        amount.append(utils.fraction_to_string(ingredient['display_number']))
    if ingredient['display_unit']:
        amount.append((ingredient['display_unit']))
    return ' '.join(amount)


def lookup_groceries(recipe):
    """Looks up grocery info for each ingredient.
    
    Sets the following keys for each scaled ingredient:
    - 'grocery' (dict)
    - 'has_matching_grocery' (bool)
    - 'grocery_count' (float)
    """

    for ingredient in ingredients_in(recipe):
        lookup_grocery(ingredient)
        ingredient['grocery_count'] = grocery_count(ingredient)
    return recipe


def lookup_grocery(ingredient):
    """Adds grocery data to ingredient."""

    ingredient['has_matching_grocery'] = False
    grocery = utils.grocery_info(ingredient['item'])

    if grocery is None:
        return
    
    ingredient['has_matching_grocery'] = True
    grocery_keys = ['name', 'cost', 'volume_amount', 'volume_unit', 
                    'weight_amount', 'weight_unit', 'other_amount', 
                    'other_unit', 'discrete_amount', 'calories', 'fat', 
                    'carbohydrates', 'protein', 'tags']
    ingredient['grocery'] = {k: grocery[k] for k in grocery_keys}
    ingredient['grocery']['nutrition'] = {
        'calories': ingredient['grocery'].pop('calories'),
        'fat': ingredient['grocery'].pop('fat'),
        'carbohydrates': ingredient['grocery'].pop('carbohydrates'),
        'protein': ingredient['grocery'].pop('protein')
    }
    ingredient['grocery']['tags'] = ingredient['grocery']['tags'].split('\n')


def grocery_count(ingredient) -> float:
    """Returns how many grocery items are in the ingredient."""

    if not ingredient['has_matching_grocery']:
        return 0
    
    ingredient_unit = ingredient['unit']

    if ingredient_unit == '':
        func = grocery_number_discrete
    elif utils.is_volume(ingredient_unit):
        func = grocery_number_volume
    elif utils.is_weight(ingredient_unit):
        func = grocery_number_weight
    else:
        func = grocery_number_other

    return func(ingredient)


def grocery_number_discrete(ingredient):
    """Number of groceries in ingredient, measured by count."""

    grocery_count = ingredient['grocery']['discrete_amount']
    if grocery_count == 0:
        return 0
    
    return ingredient['number'] / grocery_count


def grocery_number_volume(ingredient):
    """Number of groceries in ingredient, measured by volume."""

    ingredient_number = ingredient['number']
    ingredient_unit = ingredient['unit']
    grocery_number = ingredient['grocery']['volume_amount']
    grocery_unit = ingredient['grocery']['volume_unit']

    if grocery_number == 0:
        return 0
    if grocery_unit == '':
        return 0
    if not utils.is_volume(grocery_unit):
        return 0

    ingredient_unit_to_standard = utils.to_standard(ingredient_unit)
    grocery_unit_to_standard = utils.to_standard(grocery_unit)
    return (ingredient_number 
            * ingredient_unit_to_standard
            / grocery_number
            / grocery_unit_to_standard)


def grocery_number_weight(ingredient):
    """Number of groceries in ingredient, measured by weight."""

    ingredient_number = ingredient['number']
    ingredient_unit = ingredient['unit']
    grocery_number = ingredient['grocery']['weight_amount']
    grocery_unit = ingredient['grocery']['weight_unit']

    if grocery_number == 0:
        return 0
    if grocery_unit == '':
        return 0
    if not utils.is_weight(grocery_unit):
        return 0

    ingredient_unit_to_standard = utils.to_standard(ingredient_unit)
    grocery_unit_to_standard = utils.to_standard(grocery_unit)
    return (ingredient_number 
            * ingredient_unit_to_standard
            / grocery_number
            / grocery_unit_to_standard)


def grocery_number_other(ingredient):
    """Number of groceries in ingredient, measured by a nonstandard unit."""

    ingredient_number = ingredient['number']
    ingredient_unit = ingredient['unit']
    grocery_number = ingredient['grocery']['other_amount']
    grocery_unit = ingredient['grocery']['other_unit']

    if grocery_number == 0:
        return 0
    if grocery_unit == '':
        return 0
    if not utils.is_equivalent(ingredient_unit, grocery_unit):
        return 0

    return ingredient_number / grocery_number


def set_instructions(recipe):
    """Sets instruction data for each scale.
    
    Sets the following keys for each scale:
    - 'instructions' (list)
    - 'has_instructions' (bool)
    """

    for scale in recipe['scales']:
        scale['instructions'] = []
        for step in recipe['instructions']:
            if 'scale' not in step or utils.to_fraction(step['scale']) == scale['multiplier']:
                scale['instructions'].append(step.copy())
        scale['has_instructions'] = bool(scale['instructions'])

    recipe = set_instruction_lists(recipe)
    recipe = number_steps(recipe)
    return recipe


def set_instruction_lists(recipe):
    """Groups instruction steps into step lists."""
    
    for scale in recipe['scales']:
        scale['instruction_lists'] = defaultdict(list)
        for step in scale['instructions']:
            scale['instruction_lists'][step.get('list', 'Instructions')].append(step)
    return recipe


def number_steps(recipe):
    """Sets step numbers for instructions."""

    for scale in recipe['scales']:
        for steps in scale['instruction_lists'].values():
            for i, step in enumerate(steps, 1):
                step['number'] = i
    return recipe


def set_sources(recipe):
    """Sets sources data.
    
    Sets the following keys:
    - 'has_sources' (bool)

    Sets the following keys for each source:
    - 'html' (str)
    """


    if 'sources' not in recipe:
        recipe['has_sources'] = False
        return recipe
    
    for source in recipe['sources']:
        source['html'] = source_html(source)

    recipe['has_sources'] = True

    return recipe


def source_html(source):
    """Returns link html for a source."""

    if 'name' in source and 'url' in source:
        return source_link(source['name'], source['url'])
    elif  'name' in source and 'url' not in source:
        return source['name']
    elif  'name' not in source and 'url' in source:
        name = urlparse(source['url']).netloc
        return source_link(name, source['url'])
    else:
        return ''


def source_link(name, url) -> str:
    """Returns html for link given name and url."""

    return f'<a href="{url}" target="_blank">{name}</a>'


def set_notes(recipe):
    """Set notes for each scale.
    
    Sets the following keys for each scale:
    - 'notes' (list)
    - 'has_notes' (bool)
    - 'has_notes_box' (bool)
    """

    for scale in recipe['scales']:

        if 'notes' in recipe:
            scale['notes'] = notes_for_scale(recipe['notes'], scale)
        else:
            scale['notes'] = []

        scale['has_notes'] = bool(scale['notes'])
        scale['has_notes_box'] = recipe['has_sources'] or scale['has_notes']
    return recipe


def notes_for_scale(notes, scale) -> list:
    """Returns notes for a scale."""

    scale_notes = []
    for note in notes:
        if 'scale' not in note or note['scale'] == scale['multiplier']:
            scale_notes.append(note)
    return scale_notes


def set_search_targets(recipe):
    """Add search target data.
    
    Sets the following keys for each scale:
    - 'search_targets' (list)
    """

    recipe['search_targets'] = []
    recipe['search_targets'].append({
        'text': recipe['title'],
        'type': 'title'
    })

    # subtitle
    if recipe['has_subtitle']:
        recipe['search_targets'].append({
            'text': recipe['subtitle'],
            'type': 'subtitle'
        })

    # ingredient
    for ingredient in recipe['scales'][0]['ingredients']:
        recipe['search_targets'].append({
            'text': ingredient['display_item'],
            'type': 'ingredient'
        })

    # ingredient tags
    for ingredient in recipe['scales'][0]['ingredients']:
        if 'grocery' in ingredient:
            for tag in ingredient['grocery']['tags']:
                recipe['search_targets'].append({
                    'text': f'{ingredient["display_item"]} ({tag})',
                    'type': 'ingredient-tag'
                })

    for target in recipe['search_targets']:
        target['class'] = 'target-' + target['type']

    return recipe


def set_schema(recipe):
    """Add schema to recipe data.

    More on recipe schema: https://schema.org/Recipe

    Sets the following keys:
    - 'schema_str' (str)
    """

    schema = {
        '@context': 'https://schema.org',
        '@type': 'Recipe',
        'name': recipe['title']
    }

    if recipe['has_image']:
        schema['image'] = recipe['image']

    if servings_schema(recipe):
        schema['recipeYield'] = servings_schema(recipe)

    if recipe['scales'][0]['has_ingredients']:
        schema['recipeIngredient'] = []
        for ingredient in recipe['scales'][0]['ingredients']:
            schema['recipeIngredient'].append(ingredient['string'])

    recipe['schema_string'] = json.dumps(schema)
    return recipe


def servings_schema(recipe) -> str:
    """Returns schema string for servings. Empty string if no servings."""

    if recipe['scales'][0]['has_servings'] is False:
        return ''

    number = recipe['scales'][0]['servings']
    unit = 'serving' if number == 1 else 'servings'
    return f'{number} {unit}'


def load_collections(collections_path: str, log_path:str = None) -> list:
    """Generates data for collections.
    
    Args:
        collections_path: Directory that contains collections data files.
        log_path: Directory to save collection level log files.

    Returns:
        Collections data as a list of dictionaries.
    """

    has_log = log_path is not None
    if has_log:
        utils.create_dir(log_path)

    collections = []
    for file in os.listdir(collections_path):
        file_path = os.path.join(collections_path, file)

        if has_log:
            collection_log_path = os.path.join(log_path, file)
            collections.append(load_collection(file_path, collection_log_path))
        else:
            collections.append(load_collection(file_path))
    return collections


def load_collection(file_path, log_path=None) -> dict:
    """Generates data for a collection.
    
    Args:
        file_path: Directory that contains collections data files.
        log_path: Directory to save collection pipe log files.

    Returns:
        Collection data as a dictionary.
    """

    has_log = log_path is not None
    if not has_log:
        log_path = ''

    with open(file_path, 'r', encoding='utf8') as f:
        data = json.load(f)
    return utils.pipe(data,
                      log_path,
                      set_homepage,
                      set_collection_url)


def set_homepage(collection):
    """Add homepage data to collection.
    
    Sets the following keys:
    - 'is_homepage' (bool)
    """
    
    collection['is_homepage'] = False
    if collection['url_path'] == '':
        collection['is_homepage'] = True
    return collection


def set_collection_url(collection):
    """Set href to a collection from a recipe page.
    
    Sets the following keys:
    - 'href' (str)
    - 'url' (str)
    """

    if collection['is_homepage']:
        collection['href'] = '..'
    else:
        collection['href'] = f'../{collection["url_path"]}'

    url_path = '/' + collection["url_path"]
    collection['url'] = utils.make_url(path=url_path)
    feedback_name = collection['name'] + ' (Collection)'
    collection['feedback_url'] = utils.feedback_url(feedback_name, collection['url'])

    return collection


def set_child_recipe_links(site):
    """Sets link data for parent ingredients.
    
    Sets the following keys for parent ingredients:
    - 'recipe_url' (str)
    """

    for ingredient in ingredients_in(site):
        if ingredient['is_recipe']:
            ingredient['recipe_url'] = '../' + ingredient['recipe_slug']

    return site


def set_recipes_used_in(site):
    """Sets link data for child recipes.
    
    Sets the following keys for each recipe:
    - 'used_in_any' (bool)

    Sets the following keys for each child recipe:
    - 'used_in' (list)
    """

    for recipe in site['recipes']:
        recipe['used_in_any'] = False

    for parent_recipe, ingredient in ingredients_in(site, include='r'):
        if ingredient['is_recipe']:
            child_recipe = recipe_from_slug(ingredient['recipe_slug'], site['recipes'])
            child_recipe['used_in_any'] = True
            child_recipe = add_used_in(child_recipe, parent_recipe)

    # remove duplicates
    for recipe in site['recipes']:
        if recipe['used_in_any']:
            recipe['used_in'] = [dict(t) for t in {tuple(d.items()) for d in recipe['used_in']}]

    return site


def recipe_from_slug(slug, recipes):
    """Returns recipe dictionary that matches slug."""

    for recipe in recipes:
        if recipe['url_slug'] == slug:
            return recipe
        
    raise ValueError(f'Could not find recipe with slug: {slug}')


def add_used_in(child_recipe, parent_recipe):
    """Add parent recipe data to child recipe."""

    if 'used_in' not in child_recipe:
        child_recipe['used_in'] = []

    child_recipe['used_in'].append({
        'title': parent_recipe['title'],
        'slug': parent_recipe['url_slug']
    })    
    return child_recipe


def set_ingredient_as_recipe_quantities(site):
    """Sets recipe quantities for each parent ingredient.
    
    Sets the following keys for each parent ingredient:
    - 'recipe_quantity' (float)
    """

    for ingredient in ingredients_in(site):
        if ingredient['is_recipe']:
            set_recipe_quantity(ingredient, site['recipes'])
    return site


def set_recipe_quantity(ingredient, recipes) -> None:
    """Sets recipe quantity for a parent ingredient."""

    number = ingredient['number']
    unit = ingredient['unit']
    recipe = recipe_from_slug(ingredient['recipe_slug'], recipes)
    ingredient['recipe_quantity'] = recipe_quantity(number, unit, recipe)


def recipe_quantity(amount, unit, recipe) -> float:
    """Returns the number of recipes produce an amount and unit.
    
    Returns 0 if no compatible yields.
    """

    for yielb in recipe['yield']:
        yield_unit = yielb['unit']
        if (utils.is_volume(unit) and utils.is_volume(yield_unit) 
            or utils.is_weight(unit) and utils.is_weight(yield_unit)):
            return (amount
                    * utils.to_standard(unit)
                    / utils.to_standard(yield_unit)
                    / yielb['number'])
        elif utils.is_equivalent(unit, yield_unit):
            return amount / yielb['number']
    return 0


def set_costs(site):
    """Set costs for each ingredients and recipe scale.
    
    Sets the following keys for each scale:
    - 'cost' (float)
    - 'cost_final' (bool)

    Sets the following keys for each ingredient:
    - 'cost' (float)
    - 'cost_final' (bool)
    """

    for ingredient in ingredients_in(site):
        ingredient['cost_final'] = False

    for scale in scales_in(site):
        scale['cost_final'] = False

    for ingredient in ingredients_in(site, keys='explicit_cost'):
        ingredient['cost'] = ingredient['explicit_cost']
        ingredient['cost_final'] = True

    for ingredient in ingredients_in(site, values={'is_grocery': True, 'cost_final': False}):
        if not ingredient['has_matching_grocery']:
            ingredient['cost'] = 0
        else:
            ingredient['cost'] = (ingredient['grocery_count'] * ingredient['grocery']['cost'])
        ingredient['cost_final'] = True

    for recipe, scale in scales_in(site, include='r'):
        if 'explicit_cost' in recipe:
            scale['cost'] = recipe['explicit_cost'] * scale['multiplier']
            scale['cost_final'] = True

    while recipes_cost_pending_count(site):
        calculate_ingredient_costs(site)		
        pre_pending_count = recipes_cost_pending_count(site)
        calculate_recipe_costs(site)
        post_pending_count = recipes_cost_pending_count(site)
        if pre_pending_count == post_pending_count:
            raise ValueError('Cyclic recipe reference found')        

    return site


def recipes_cost_pending_count(site) -> int:
    """Number of recipe scales where cost_final is False."""

    count = 0
    for scale in scales_in(site):
        if not scale['cost_final']:
            count += 1
    return count


def calculate_ingredient_costs(site) -> None:
    """Tries to calculate costs of parent ingredients. 
    
    Sets ingredient cost if child recipe's cost is final.
    """

    for ingredient in ingredients_in(site):
        if ingredient['is_recipe']:
            child_recipe = recipe_from_slug(ingredient['recipe_slug'], site['recipes'])
            if child_recipe['scales'][0]['cost_final']:
                ingredient['recipe_cost'] = child_recipe['scales'][0]['cost']
                ingredient['cost'] = ingredient['recipe_quantity'] * ingredient['recipe_cost']
                ingredient['cost_final'] = True


def calculate_recipe_costs(site) -> None:
    """Tries to calculate costs of recipes.
    
    Sets recipe cost if all ingredients' costs are final.
    """

    for scale in scales_in(site):
        if not scale['cost_final'] and ingredients_costs_final(scale):
            scale['cost'] = sum_ingredient_cost(scale)
            scale['cost_final'] = True


def ingredients_costs_final(scale):
    """True if all ingredients' costs are final."""

    for ingredient in scale['ingredients']:
        if not ingredient['cost_final']:
            return False
    return True


def sum_ingredient_cost(scale) -> float:
    """Returns the cost of a scale by adding each ingredient."""

    cost = 0
    for ingredient in scale['ingredients']:
        cost += ingredient['cost']
    return cost


def set_costs_per_serving(site):
    """Sets cost per serving for each ingredient and recipe scale.

    Sets the following keys for each scale:
    - 'cost_per_serving' (float)    
    
    Sets the following keys for each ingredient:
    - 'cost_per_serving' (float)
    """

    for scale in scales_in(site):
        servings = scale['servings'] if scale['has_servings'] else 1
        scale['cost_per_serving'] = scale['cost'] / servings

    for scale, ingredient in ingredients_in(site, include='s'):
        servings = scale['servings'] if scale['has_servings'] else 1
        ingredient['cost_per_serving'] = ingredient['cost'] / servings

    return site


def set_cost_strings(site):
    """Sets formatted cost strings for ingredients and scales.

    Sets the following keys for each ingredient:
    - 'cost_string' (str)
    - 'cost_per_serving_string' (str)

    Sets the following keys for each scale:
    - 'cost_string' (str)
    - 'cost_per_serving_string' (str)
    - 'has_visible_cost' (bool)
    - 'has_visible_cost_per_serving' (bool)
    """

    for ingredient in ingredients_in(site):
        ingredient['cost_string'] = utils.format_currency(ingredient['cost'])
        ingredient['cost_per_serving_string'] = utils.format_currency(ingredient['cost_per_serving'])

    for recipe, scale in scales_in(site, include='r'):
        scale['cost_string'] = utils.format_currency(scale['cost'])
        scale['cost_per_serving_string'] = utils.format_currency(scale['cost_per_serving'])
        scale['has_visible_cost'] = (not recipe['hide_cost']
                                     and bool(scale['cost'] > 0))
        scale['has_visible_cost_per_serving'] = (scale['has_visible_cost']
                                                 and scale['has_servings']
                                                 and scale['servings'] != 1)
    return site


def set_nutrition(site):
    """Set nutrition for each ingredients and recipe scale.
    
    Sets the following keys for each scale:
    - 'nutrition' (dict)
    - 'nutrition_final' (bool)

    Sets the following keys for each ingredient:
    - 'nutrition' (dict)
    - 'nutrition_final' (bool)
    - 'has_nutrition' (bool)
    """


    for ingredient in ingredients_in(site):
        ingredient['nutrition_final'] = False

    for scale in scales_in(site):
        scale['nutrition_final'] = False

    for ingredient in ingredients_in(site, keys='explicit_nutrition'):
        ingredient['nutrition'] = ingredient['explicit_nutrition']
        ingredient['has_nutrition'] = True
        ingredient['nutrition_final'] = True
    
    for recipe, scale, ingredient in ingredients_in(site, values={'is_grocery': True, 'nutrition_final': False}, include='rs'):
        if not ingredient['has_matching_grocery']:
            ingredient['nutrition'] = empty_nutrition()
            ingredient['has_nutrition'] = False
        else:
            ingredient['nutrition'] = multiply_nutrition(
                ingredient['grocery']['nutrition'], 
                ingredient['grocery_count']
                )
            ingredient['has_nutrition'] = True
        ingredient['nutrition_final'] = True

    for recipe, scale in scales_in(site, include='r'):
        if 'explicit_nutrition' in recipe:
            scale['nutrition'] = multiply_nutrition(recipe['explicit_nutrition'], scale['multiplier'])
            scale['nutrition_final'] = True

    while recipes_nutrition_pending_count(site):
        calculate_ingredient_nutrition(site)
        pre_pending_count = recipes_nutrition_pending_count(site)
        calculate_recipes_nutrition(site)
        post_pending_count = recipes_nutrition_pending_count(site)
        if pre_pending_count == post_pending_count:
            raise ValueError('Cyclic recipe reference found')

    return site

# todo has_nutrition to flags


def recipes_nutrition_pending_count(site) -> int:
    """Number of recipe scales where nutrition_final is False."""

    count = 0
    for scale in scales_in(site):
        if not scale['nutrition_final']:
            count += 1
    return count


def calculate_ingredient_nutrition(site) -> None:
    """Tries to calculate nutrition of parent ingredients. 
    
    Sets ingredient nutrition if child recipe's nutrition is final.
    """

    for ingredient in ingredients_in(site):
        if ingredient['is_recipe']:
            child_recipe = recipe_from_slug(ingredient['recipe_slug'], 
                                            site['recipes'])
            if child_recipe['scales'][0]['nutrition_final']:
                ingredient['recipe_nutrition'] = child_recipe['scales'][0]['nutrition']
                ingredient['nutrition'] = multiply_nutrition(
                    ingredient['recipe_nutrition'], 
                    ingredient['recipe_quantity'])
                ingredient['has_nutrition'] = True
                ingredient['nutrition_final'] = True


def calculate_recipes_nutrition(site):
    """Tries to calculate nutrition of recipes.
    
    Sets recipe nutrition if all ingredients' nutritions are final.
    """

    for scale in scales_in(site):
        if not scale['nutrition_final'] and ingredients_nutrition_final(scale):
            scale['nutrition'] = sum_ingredient_nutrition(scale)
            scale['nutrition_final'] = True


def ingredients_nutrition_final(scale):
    """True if all ingredients' nutritions are final."""

    for ingredient in scale['ingredients']:
        if not ingredient['nutrition_final']:
            return False
    return True


def sum_ingredient_nutrition(scale) -> dict:
    """Returns the nutrition of a scale by adding each ingredient."""

    nutrition = empty_nutrition()
    for ingredient in scale['ingredients']:
        nutrition['calories'] += ingredient['nutrition']['calories']
        nutrition['fat'] += ingredient['nutrition']['fat']
        nutrition['protein'] += ingredient['nutrition']['protein']
        nutrition['carbohydrates'] += ingredient['nutrition']['carbohydrates']
    return nutrition




def multiply_nutrition(nutrition, multiplier, round_result=False) -> dict:
    """Multiplies nutrition values by a given multiplier.
    
    Optionally, the results can be rounded to the nearest integer.
    """

    multiplied = {
        'calories': nutrition['calories'] * multiplier,
        'fat': nutrition['fat'] * multiplier,
        'carbohydrates': nutrition['carbohydrates'] * multiplier,
        'protein': nutrition['protein'] * multiplier
    }

    if round_result:
        multiplied = {
            'calories': round(multiplied['calories']),
            'fat': round(multiplied['fat']),
            'carbohydrates': round(multiplied['carbohydrates']),
            'protein': round(multiplied['protein'])
        }

    return multiplied


def empty_nutrition() -> dict:
    """Returns a nutrition with zero values."""

    return {
        'calories': 0,
        'fat': 0,
        'carbohydrates': 0,
        'protein': 0
    }


def set_display_nutrition(site):
    """Sets nutrition to display for each scale and each ingredient.

    If servings are set, nutrition to display is nutrition per serving,
    otherwise, it is the total nutrition.
    
    Sets the following keys for each scale:
    - 'nutrition_display' (dict)
    - 'has_visible_nutrition' (bool)
    - 'is_nutrition_per_serving' (bool)

    Sets the following keys for each ingredient:
    - 'nutrition_display' (dict)    
    """

    for scale, ingredient in ingredients_in(site, include='s'):
        servings = scale.get('servings', 1)
        ingredient['nutrition_display'] = multiply_nutrition(
            ingredient['nutrition'], 1 / servings, round_result=True)

    for recipe, scale in scales_in(site, include='r'):
        servings = scale.get('servings', 1)
        scale['nutrition_display'] = multiply_nutrition(
            scale['nutrition'], 1 / servings, round_result=True)
        scale['has_visible_nutrition'] = scale_has_visible_nutrition(scale, recipe)
        scale['is_nutrition_per_serving'] = servings != 1

    return site


def scale_has_visible_nutrition(scale, recipe) -> bool:
    """Determines if a scale's nutrition should be visible."""

    if recipe['hide_nutrition']:
        return False
    if 'explicit_nutrition' in recipe:
        return True
    return has_nutrients(scale['nutrition'])


def has_nutrients(nutrition: dict):
    """Return True if any item in nutrition is nonzero."""

    for value in nutrition.values():
        if value > 0:
            return True
    return False


def set_ingredient_details(site):
    """Sets ingredient detail info.
    
    Sets the following keys for each recipe:
    - 'has_cost_detail' (bool)
    - 'has_cost_per_serving_detail' (bool)
    - 'has_nutrition_detail' (bool)

    Sets the following keys for each scale:
    - 'has_cost_detail' (bool)
    - 'has_cost_per_serving_detail' (bool)
    - 'has_nutrition_detail' (bool)
    - 'has_any_detail' (bool)
    """

    for recipe, scale in scales_in(site, include='r'):
        explicit_cost = 'explicit_cost' in recipe
        explicit_nutrition = 'explicit_nutrition' in recipe
        cost_hidden = recipe['hide_cost']
        scale['has_cost_detail'] = (
            has_cost_detail(scale) 
            and not cost_hidden 
            and not explicit_cost)
        scale['has_cost_per_serving_detail'] = (
            scale['has_cost_detail']
            and scale['has_servings'])
        scale['has_nutrition_detail'] = (
            scale['has_visible_nutrition']
            and not explicit_nutrition)
        scale['has_any_detail'] = (
            scale['has_cost_detail'] 
            or scale['has_cost_per_serving_detail'] 
            or scale['has_nutrition_detail'])

    for recipe in site['recipes']:
        recipe['has_cost_detail'] = False
        recipe['has_cost_per_serving_detail'] = False
        recipe['has_nutrition_detail'] = False
        for scale in recipe['scales']:
            if scale['has_cost_detail']:
                recipe['has_cost_detail'] = True
            if scale['has_cost_per_serving_detail']:
                recipe['has_cost_per_serving_detail'] = True
            if scale['has_nutrition_detail']:
                recipe['has_nutrition_detail'] = True

    return site


def has_cost_detail(scale) -> bool:
    """True if any ingredient has nonzero cost."""

    for ingredient in scale['ingredients']:
        if ingredient['cost']:
            return True
    return False


def has_nutrition_detail(scale) -> bool:
    """True if any ingredient has nutrition detail."""

    for ingredient in scale['ingredients']:
        if ingredient['has_nutrition']:
            return True
    return False


def set_description_areas(site):
    """Sets recipe data regarding the description area.
    
    Sets the following keys for each scale:
    - 'has_description_area' (bool)
    """

    for recipe, scale in scales_in(site, include='r'):
        scale['has_description_area'] = (
            scale['has_visible_yields'] 
            or scale['has_visible_serving_sizes'] 
            or scale['has_times'] 
            or scale['has_visible_cost'] 
            or recipe['has_description'] 
            or recipe['used_in_any'])
    return site


def set_ingredient_lists(site):
    """Groups ingredients into ingredient lists.
    
    Sets the following keys for each scale:
    - 'ingredient_lists' (dict)
    """

    for scale in scales_in(site):
        scale['ingredient_lists'] = defaultdict(list)
        for ingredient in scale['ingredients']:
            scale['ingredient_lists'][ingredient.get('list', 'Ingredients')].append(ingredient)
    return site


def link_recipes_collections(site):
    """Adds collections data to recipes and vice versa.
    
    Sets the following keys for each recipe:
    - 'collections' (list)

    Sets the following keys for each collection:
    - 'recipes' (list)
    """

    for recipe in site['recipes']:
        recipe['collections'] = []

    for collection in site['collections']:
        for i, url_slug in enumerate(collection['recipes']):
            for recipe in site['recipes']:
                if recipe['url_slug'] == url_slug:
                    recipe['collections'].append(info_for_recipe(collection))
                    collection['recipes'][i] = info_for_collection(recipe)

    return site


def info_for_collection(recipe) -> dict:
    """Recipe data needed for collection page."""

    keys = ('title', 'url_slug', 'subtitle', 'has_subtitle', 'image_url', 
            'search_targets')
    return {k: recipe[k] for k in keys if k in recipe}


def info_for_recipe(collection) -> dict:
    """Collection data needed for recipe page."""

    keys = ('name', 'url_path', 'label', 'href')
    return {k: collection[k] for k in keys if k in collection}


def set_search_values(site):
    """Adds data needed for search function.

    Sets the following keys for each collection:
    - 'search_group_interval' (int)
    
    Sets the following keys for each recipe in collection:
    - 'index' (int)
    """

    for collection in site['collections']:
        for i, recipe in enumerate(collection['recipes'], 1):
            recipe['index'] = i
        collection['search_group_interval'] = 10 ** math.ceil(math.log10(i))

    return site


def set_summary(site):
    """Adds summary data to site.
    
    Sets the following keys for the site:
    - 'summary' (dict)
    """

    site['summary'] = {
        'recipes': summary_recipes(site),
        'collections': summary_collections(site),
        'ingredients': summary_ingredients(site)
        }
    return site


def summary_recipes(site):
    """Summary data for recipes."""

    recipes = []
    for recipe in site['recipes']:
        recipes.append({
            'title': recipe['title'],
            'collections': [c['name'] for c in recipe['collections']]
        })
    return recipes


def summary_collections(site):
    """Summary data for collections."""
    
    collections = []
    for collection in site['collections']:
        collections.append({
            'name': collection['name'],
            'recipes': [r['title'] for r in collection['recipes']]
        })
    return collections


def summary_ingredients(site: dict) -> list[dict]:
    """Summary data for ingredients."""

    ingredients = []
    for recipe, scale, ingredient in ingredients_in(site, include='rs'):
        ingredients.append({
            'recipe': recipe['title'],
            'scale': scale['label'],
            'ingredient': ingredient['string'],
            'found_grocery': ingredient['has_matching_grocery'],
            'number_groceries': round(ingredient.get('grocery_count', 0),5)
        })
    return ingredients


def ingredients_in(container:(dict | list), keys:(str | list) = None, 
                   values:dict = None, include:str = None) -> list:
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
        include = ''
    if keys is None:
        keys = []
    if isinstance(keys, str):
        keys = [keys]

    ingredients = []
    for recipe in container_to_recipes(container):
        for scale in recipe['scales']:
            for ingredient in scale['ingredients']:
                if ingredient_matches_criteria(ingredient, keys, values):
                    item_list = []
                    if 'r' in include:
                        item_list.append(recipe)
                    if 's' in include:
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

    if 'recipes' in container.keys():
        return container['recipes']
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
        include = ''

    scales = []
    for recipe in container_to_recipes(container):
        for scale in recipe['scales']:
            item_list = []
            if 'r' in include:
                item_list.append(recipe)
            item_list.append(scale)

            if len(item_list) == 1:
                scales.append(item_list[0])
            else:
                scales.append(tuple(item_list))

    return scales


def build_site(site: dict, site_path: str, local=False, verbose=False) -> None:
    """Builds a recipe site using site data.

    Args:
        site: Site data as a dictionary.
        site_path: Path to build the site inside.
        local: Builds local version if true, web version otherwise. Defaults is False.
    """
    
    utils.make_empty_dir(site_path)

    for recipe in site['recipes']:
        recipe_dir = os.path.join(site_path, recipe['url_slug'])
        make_recipe_page(recipe, recipe_dir, local)
        utils.make_qr_file(recipe['url'], os.path.join(recipe_dir, 'recipe-qr.png'))
        make_print_page(recipe, os.path.join(recipe_dir, 'p'), local)
        if recipe['has_image']:
            shutil.copyfile(
                recipe['image_src_path'],
                os.path.join(recipe_dir, recipe['image']))
        if verbose:
            print(f'Recipe: {recipe["title"]}')

    for collection in site['collections']:
        collection_dir = get_collection_dir(collection, site_path)
        make_collection_page(collection, collection_dir, local)
        if verbose:
            print(f'Collection: {collection["name"]}')

    make_404_page(os.path.join(site_path, 'error.html'))
    make_summary_page(site, os.path.join(site_path, 'summary.html'))

    shutil.copyfile(
        os.path.join(utils.assets_directory, 'icon.png'), 
        os.path.join(site_path, 'icon.png'))
    shutil.copyfile(
        os.path.join(utils.assets_directory, 'default_720x540.jpg'), 
        os.path.join(site_path, 'default.jpg'))


def get_collection_dir(collection: dict, site_path: str) -> str:
    """Returns site directory for a collection page."""

    if collection['is_homepage']:
        return site_path
    return os.path.join(site_path, collection['url_path'])


def make_recipe_page(recipe: dict, dir: str, local: bool) -> None:
    """Create index.html file for recipe page.

    Args:
        recipe: Recipe data as a dictionary.
        dir: Path to build the page inside.
        local: Builds local version if true, web version otherwise.
    """

    utils.create_dir(dir)
    file = os.path.join(dir, 'index.html')
    content = utils.render_template('recipe-page.html', 
                              r=recipe, 
                              icon=utils.icon,
                              site_title=utils.site_title(),
                              is_local=local)
    utils.write_file(content, file)


def make_print_page(recipe: dict, dir: str, local: bool) -> None:
    """Create index.html file for recipe print page.

    Args:
        recipe: Recipe data as a dictionary.
        dir: Path to build the page inside.
        local: Builds local version if true, web version otherwise.
    """

    utils.create_dir(dir)
    file = os.path.join(dir, 'index.html')
    content = utils.render_template('print-page.html', 
                              r=recipe, 
                              is_local=local,
                              site_title=utils.site_title(),
                              icon=utils.icon)
    utils.write_file(content, file)


def make_collection_page(collection: dict, dir: str, local: bool) -> None:
    """Create index.html file for collection page.

    Args:
        collection: Collection data as a dictionary.
        dir: Path to build the page inside.
        local: Builds local version if true, web version otherwise.
    """

    utils.create_dir(dir)
    file = os.path.join(dir, 'index.html')
    content = utils.render_template('collection.html', 
                              c=collection,
                              is_local=local,
                              site_title=utils.site_title(),
                              icon=utils.icon)
    utils.write_file(content, file)


def make_summary_page(site: dict, page_path: str) -> None:
    """Create summary page for recipe site.

    Args:
        site: Site data as a dictionary.
        page_path: File path for summary page.
    """

    content = utils.render_template('summary-page.html', 
                              recipes=site['summary']['recipes'], 
                              collections=site['summary']['collections'],
                              ingredients=site['summary']['ingredients'],
                              site_title=utils.site_title())
    utils.write_file(content, page_path)


def make_404_page(page_path: str) -> None:
    content = utils.render_template('404.html', 
                              site_title=utils.site_title())
    utils.write_file(content, page_path)


if __name__ == "__main__":
    build()