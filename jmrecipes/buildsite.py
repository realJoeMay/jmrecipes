import os
import datetime
import shutil
import json
from collections import defaultdict
from urllib.parse import urlparse

import parser
import utils
from utils import builds_directory, data_directory, assets_directory, create_dir, make_empty_dir, write_file, render_template
from utils import site_title, feedback_url, icon, fraction_to_string, make_url, to_fraction



def build():
    """Loads site data and creates a recipe website."""

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
    return utils.pipe(site, log_path, link_site, set_summary)


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

    recipe = parser.parse_recipe(filepath)
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
                set_image,
                set_scales,
                set_times,
                scale_yields,
                set_servings,
                set_visible_yields,
                set_visible_serving_sizes,
                set_copy_ingredients_sublabel,
                scale_ingredients,
                set_ingredient_outputs,
                lookup_groceries,
                set_ingredients_cost,
                set_ingredients_cost_per_serving,
                set_ingredients_nutrition,
                set_ingredient_lists,
                set_recipe_costs,
                set_recipe_cost_per_serving,
                set_recipe_nutrition,
                set_ingredient_details,
                set_instructions,
                set_has_description_area,
                set_sources,
                scale_notes,
                set_notes,
                set_schema
                )


def set_defaults(recipe):

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
    """Sets values regarding the URLs."""

    recipe['url_path'] = '/' + recipe['url_slug']
    recipe['url'] = make_url(path=recipe['url_path'])
    recipe['feedback_url'] = feedback_url(recipe['title'], recipe['url'])
    return recipe


def set_subtitle(recipe: dict) -> dict:
    """Sets values regarding the recipe subtitle."""
    
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
    """Sets basic data for each recipe scale."""

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


def set_times(recipe: dict) -> dict:
    """Set recipe attributes related cook times."""

    for time in recipe['times']:

        if 'unit' not in time or time['unit'] == '':
            time['unit'] = 'minutes' if time['time'] > 1 else 'minute'

        time_string = fraction_to_string(time['time'])
        time['time_string'] = f'{time_string} {time["unit"]}'

    for scale in recipe['scales']:
        scale['times'] = recipe['times']
        scale['has_times'] = bool(scale['times'])

    return recipe


def set_yield_defaults(recipe):
    """Set default values for each yield."""

    for yielb in recipe['yield']:
        if yielb['show_yield'] == '':
            yielb['show_yield'] = True
        if yielb['show_serving_size'] == '':
            yielb['show_serving_size'] = False
    return recipe


def scale_yields(recipe):
    """Add yield section to each recipe scale."""

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
    """Set servings data for each scale in recipe."""

    for scale in recipe['scales']:
        set_servings_scale(scale)
    recipe['has_servings'] = recipe['scales'][0]['has_servings']
    return recipe


def set_servings_scale(scale):
    """Set servings data for a recipe scale."""

    scale['has_servings'] = False
    for yielb in scale['yield']:
        if yielb['unit'].lower() in ('serving', 'servings'):
            scale['servings'] = yielb['number']
            scale['has_servings'] = True
    # return scale


def set_visible_yields(recipe):
    """Sets yield data to show on page."""

    for scale in recipe['scales']:
        scale = set_visible_yields_scale(scale)
    return recipe


def set_visible_yields_scale(scale):
    """Sets yield data for a recipe scale to show on page."""

    scale['has_visible_yields'] = False
    for yielb in scale['yield']:
        if yielb['show_yield']:
            scale['has_visible_yields'] = True
            yielb['yield_string'] = yield_string(yielb)
    return scale


def yield_string(yielb: dict) -> str:
    """Returns string for a yield."""

    number = fraction_to_string(yielb["number"])
    display = f'{number} {yielb["unit"]}'
    return display


def set_visible_serving_sizes(recipe):
    """"""

    for scale in recipe['scales']:
        scale = set_serving_size(scale)
    return recipe


def set_serving_size(scale):
    """Sets servings size data for a recipe scale to show on page."""

    scale['has_visible_serving_sizes'] = False

    if scale['has_servings'] is False:
        return scale
    
    for yielb in scale['yield']:
        if yielb['show_serving_size']:
            scale['has_visible_serving_sizes'] = True
            number = yielb['number'] / scale['servings']
            number_string = fraction_to_string(number)
            unit = utils.numberize(yielb['unit'], number)
            yielb['serving_size_string'] = f'{number_string} {unit}'
    return scale


def set_copy_ingredients_sublabel(recipe: dict) -> dict:
    """Set sublabel of copy ingredients button for each scale."""

    for scale in recipe['scales']:
        scale['copy_ingredients_sublabel'] = copy_ingredients_sublabel(scale)
    return recipe


def copy_ingredients_sublabel(scale) -> str:

    if scale['multiplier'] == 1:
        return ''
    
    if scale['has_servings']:
        unit = 'serving' if scale['servings'] ==1 else 'servings'
        return f'for {scale["servings"]} {unit}'
    
    return f'for {scale["multiplier"]}x'


def scale_ingredients(recipe):
    """Add ingredients list to each recipe scale."""

    for scale in recipe['scales']:
        scale['ingredients'] = ingredients_in_scale(recipe['ingredients'], 
                                                 scale['multiplier'])
        scale['has_ingredients'] = bool(scale['ingredients'])
    return recipe


def ingredients_in_scale(base_ingredients, multiplier) -> list:
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
            ingredients.append(multiply_ingredient(ingredient, multiplier))
        elif to_fraction(ingredient['scale']) == multiplier:        
            ingredients.append(ingredient)
    return ingredients


def multiply_ingredient(ingredient, multiplier):
    """Returns ingredient data scaled by multiplier."""

    scaled = ingredient.copy()
    scaled['number'] = ingredient['number'] * multiplier
    scaled['display_number'] = ingredient['display_number'] * multiplier
    return scaled


def set_ingredient_outputs(recipe: dict) -> dict:
    """Sets recipe data regarding ingredients."""

    for scale in recipe['scales']:
        for ingredient in scale['ingredients']:
            ingredient = set_ingredient_displays(ingredient)
            ingredient['string'] = ingredient_string(ingredient)
            ingredient['display_amount'] = ingredient_display_amount(ingredient)
    return recipe


def set_ingredient_displays(ing: dict) -> dict:
    """Fill missing ingredient display data."""

    if ing['display_number'] == 0:
        ing['display_number'] = ing['number']
    if ing['display_unit'] == '':
        ing['display_unit'] = ing['unit']
    if ing['display_item'] == '':
        ing['display_item'] = ing['item']
    return ing


def ingredient_string(ing: dict) -> str:
    """Returns string with ingredient number, unit, and item."""

    i_str = []
    if ing['display_number']:
        i_str.append(fraction_to_string(ing['display_number']))
    if ing['display_unit']:
        i_str.append((ing['display_unit']))
    if ing['display_item']:
        i_str.append((ing['display_item']))
    string = ' '.join(i_str)
    return string


def ingredient_display_amount(ingredient):
    """Return string with ingredient number and unit."""

    amount = []
    if ingredient['display_number']:
        amount.append(fraction_to_string(ingredient['display_number']))
    if ingredient['display_unit']:
        amount.append((ingredient['display_unit']))
    return ' '.join(amount)


def lookup_groceries(recipe):
    """Looks up grocery info for each ingredient."""

    for scale in recipe['scales']:
        for ingredient in scale['ingredients']:
            ingredient = lookup_grocery(ingredient)
            ingredient['grocery_number'] = grocery_number(ingredient)
    return recipe


def lookup_grocery(ingredient):
    """Returns ingredient with grocery data."""

    ingredient['has_grocery'] = False
    grocery = utils.grocery_info(ingredient['item'])

    if grocery is None:
        return ingredient
    
    ingredient['has_grocery'] = True
    grocery_keys = ["name", "cost", "volume_amount", "volume_unit", 
                    "weight_amount", "weight_unit", "other_amount", 
                    "other_unit", "discrete_amount", "Calories", "fat", 
                    "carbohydrates", "protein"]
    ingredient['grocery'] = {k: grocery[k] for k in grocery_keys}
    return ingredient


def grocery_number(ingredient):
    """Returns how many grocery items are in the ingredient."""

    if ingredient['has_grocery'] is False:
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
    """Number of groceries in ingredient, measured by volume.
    
    Returns 0 if any of the following:
    - grocery data does not include number or unit
    - listed grocery volume unit is not a known volume unit
    """

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
    """Number of groceries in ingredient, measured by an abnormal unit."""

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


def set_ingredients_cost(recipe):
    """Sets cost data for each ingredient."""

    for scale in recipe['scales']:
        for ingredient in scale['ingredients']:
            ingredient = set_ingredient_cost(ingredient)
    return recipe


def set_ingredient_cost(ingredient):
    """Set cost data for ingredient.
    
    If cost is already set, then type is explicit. Otherwise, tries to 
    calculate from grocery information. Saves cost as 0 if any there is no 
    matching grocery item or no grocery amount.

    Args:
        ingredient: Directory for a recipe's data.

    Returns:
        ingredient data as a dictionary with keys 'cost', 'cost_string' and 
        'cost_info'
    """

    if 'cost' in ingredient:
        ingredient['cost_info'] = 'explicit'
    elif not ingredient['has_grocery']:
        ingredient['cost'] = 0
        ingredient['cost_info'] = 'no grocery item'
    elif ingredient['grocery_number'] == 0:
        ingredient['cost'] = 0
        ingredient['cost_info'] = 'no grocery amount'
    elif ingredient['grocery']['cost'] == 0:
        ingredient['cost'] = 0
        ingredient['cost_info'] = 'no grocery cost'
    else:
        ingredient['cost'] = (ingredient['grocery_number'] 
                              * ingredient['grocery']['cost'])
        ingredient['cost_info'] = 'calculated'

    ingredient['cost_string'] = utils.format_currency(ingredient['cost'])
    return ingredient


def set_ingredients_cost_per_serving(recipe):
    """Sets cost per serving data for each ingredient."""

    for scale in recipe['scales']:
        if scale['has_servings']:
            servings = scale['servings']
        else:
            servings = 1

        for ingredient in scale['ingredients']:
            ingredient['cost_per_serving'] = ingredient['cost'] / servings
            ingredient['cost_per_serving_string'] = utils.format_currency(ingredient['cost_per_serving'])
     
    return recipe


def set_ingredients_nutrition(recipe):
    """Sets nutrition data for each ingredient."""

    for scale in recipe['scales']:
        for ingredient in scale['ingredients']:
            ingredient['has_nutrition'] = ingredient_has_nutrition(ingredient, scale['has_servings'])
            if ingredient['has_nutrition']:
                ingredient['nutrition'] = ingredient_nutrition(ingredient, scale['servings'])
    return recipe


def ingredient_has_nutrition(ingredient, has_servings):
    """Return True if ingredient will have nutrition information."""

    # explicit or not, requires servings
    if not has_servings:
        return False
    
    return 'explicit_nutrition' in ingredient or ingredient['has_grocery']


def ingredient_nutrition(ingredient, servings):
    """Returns nutrition per serving for an ingredient."""

    if 'explicit_nutrition' in ingredient:
        calories = ingredient['explicit_nutrition']['calories']
        fat = ingredient['explicit_nutrition']['fat']
        protein = ingredient['explicit_nutrition']['protein']
        carbohydrates = ingredient['explicit_nutrition']['carbohydrates']
    else:
        grocery_number = ingredient['grocery_number']
        calories = ingredient['grocery']['Calories'] * grocery_number
        fat = ingredient['grocery']['fat'] * grocery_number
        protein = ingredient['grocery']['carbohydrates'] * grocery_number
        carbohydrates = ingredient['grocery']['protein'] * grocery_number

    return {
        'calories': round(calories / servings),
        'fat': round(fat / servings),
        'carbohydrates': round(carbohydrates / servings),
        'protein': round(protein / servings)
    }


def set_recipe_costs(recipe):
    """Set recipe cost for each scale."""

    for scale in recipe['scales']:
        if 'explicit_cost' in recipe:
            scale['cost'] = recipe['explicit_cost'] * scale['multiplier']
        else:
            scale['cost'] = sum_ingredient_cost(scale)
        scale['cost_string'] = utils.format_currency(scale['cost'])
        scale['has_visible_cost'] = (not recipe['hide_cost']
                                     and bool(scale['cost'] > 0))
    return recipe


def sum_ingredient_cost(scale: dict):
    """Returns the cost of a scale by adding each ingredient.
    
    Args:
        scale: Dictionary for a recipe scale's data.

    Returns:
        Scale cost as float.
    """

    cost = 0
    for ingredient in scale['ingredients']:
        cost += ingredient['cost']
    return cost


def set_recipe_cost_per_serving(recipe):
    """Sets cost per serving data for each scale."""

    for scale in recipe['scales']:
        if scale['has_servings'] and scale['servings'] != 0:
            scale['cost_per_serving'] = scale['cost'] / scale['servings']
            scale['cost_per_serving_string'] = utils.format_currency(scale['cost_per_serving'])
        scale['has_visible_cost_per_serving'] = (scale['has_visible_cost']
                                                 and scale['has_servings']
                                                 and scale['servings'] != 1)
    return recipe


def set_recipe_nutrition(recipe):
    """Set recipe nutrition for each scale."""

    if recipe['hide_nutrition']:
        for scale in recipe['scales']:
            scale['has_visible_nutrition_per_serving'] = False
        return recipe

    if not recipe['has_servings']:
        for scale in recipe['scales']:
            scale['has_visible_nutrition_per_serving'] = False
        return recipe

    if 'explicit_nutrition' in recipe:
        for scale in recipe['scales']:
            multiplier = scale['multiplier'] / scale['servings']
            scale['nutrition'] = scale_nutrition(recipe['explicit_nutrition'], multiplier)
            scale['has_visible_nutrition_per_serving'] = True
            scale['nutrition_source'] = 'explicit'
        return recipe

    # nutrition not explicit
    for scale in recipe['scales']:
        scale['nutrition'] = sum_ingredient_nutrition(scale)
        scale['has_visible_nutrition_per_serving'] = (has_nutrients(scale['nutrition']))
        scale['nutrition_source'] = 'ingredients'
    return recipe


def scale_nutrition(nutrition, multiplier):

    scaled = {}
    for nutrient in nutrition:
        scaled[nutrient] = round(float(nutrition[nutrient] * multiplier))

    return scaled


def sum_ingredient_nutrition(scale):

    sum = {
        'calories': 0,
        'fat': 0,
        'protein': 0,
        'carbohydrates': 0
    }
    for ingredient in scale['ingredients']:
        if ingredient['has_nutrition']:
            for nutrient in sum:
                sum[nutrient] += ingredient['nutrition'][nutrient]

    return sum


def has_nutrients(nutrition: dict):
    """Return True if any item in nutrition is nonzero."""

    for value in nutrition.values():
        if value > 0:
            return True
    return False


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


def set_ingredient_details(recipe):
    """Sets ingredient detail info."""

    explicit_cost = 'explicit_cost' in recipe
    explicit_nutrition = 'explicit_nutrition' in recipe
    cost_hidden = recipe['hide_cost']
    nutrition_hidden = recipe['hide_nutrition']

    for scale in recipe['scales']:

        scale['has_cost_detail'] = (
            has_cost_detail(scale) 
            and not cost_hidden 
            and not explicit_cost)
        
        scale['has_cost_per_serving_detail'] = (
            scale['has_cost_detail']
            and scale['has_servings'])
        
        scale['has_nutrition_per_serving_detail'] = (
            has_nutrition_detail(scale)
            and scale['has_servings']
            and scale['has_visible_nutrition_per_serving']
            and not explicit_nutrition
            and not nutrition_hidden)
                            
        scale['has_any_detail'] = (
            scale['has_cost_detail'] 
            or scale['has_cost_per_serving_detail'] 
            or scale['has_nutrition_per_serving_detail'])
        
    recipe['has_cost_detail'] = False
    recipe['has_cost_per_serving_detail'] = False
    recipe['has_nutrition_per_serving_detail'] = False
    for scale in recipe['scales']:
        if scale['has_cost_detail']:
            recipe['has_cost_detail'] = True
        if scale['has_cost_per_serving_detail']:
            recipe['has_cost_per_serving_detail'] = True
        if scale['has_nutrition_per_serving_detail']:
            recipe['has_nutrition_per_serving_detail'] = True

    return recipe


def has_cost_detail(scale):
    """True if any ingredient has cost detail."""

    for ingredient in scale['ingredients']:
        if ingredient['cost']:
            return True
    return False


def has_nutrition_detail(scale):
    """True if any ingredient has nutrition detail."""

    for ingredient in scale['ingredients']:
        if ingredient['has_nutrition']:
            return True
    return False


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
        scale['has_description_area'] = (scale['has_visible_yields']
                                         or scale['has_visible_serving_sizes']
                                         or scale['has_times']
                                         or scale['has_visible_cost'])
    return recipe


def set_sources(recipe):
    """"""

    if 'sources' not in recipe:
        recipe['has_sources'] = False
        return recipe
    
    for source in recipe['sources']:
        source['html'] = source_html(source)

    recipe['has_sources'] = True

    return recipe


def source_html(source):
    """Returns html for a source."""

    if 'name' in source and 'url' in source:
        return source_link(source['name'], source['url'])
    elif  'name' in source and 'url' not in source:
        return source['name']
    elif  'name' not in source and 'url' in source:
        name = urlparse(source['url']).netloc
        return source_link(name, source['url'])
    else:
        return ''


def source_link(name, url):

    return f'<a href="{url}" target="_blank">{name}</a>'


def scale_notes(recipe):
    """Set notes for each scale."""

    if 'notes' not in recipe:
        for scale in recipe['scales']:
            scale['notes'] = []
        return recipe
    
    for scale in recipe['scales']:
        scale['notes'] = notes_for_scale(recipe['notes'], scale)
    return recipe


def notes_for_scale(notes, scale):
    """Returns notes for a scale."""

    scale_notes = []
    for note in notes:
        if 'scale' not in note or note['scale'] == scale['multiplier']:
            scale_notes.append(note)
    return scale_notes


def set_notes(recipe):

    for scale in recipe['scales']:
        scale['has_notes'] = bool(scale['notes'])
        scale['has_notes_box'] = recipe['has_sources'] or scale['has_notes']
    return recipe


def set_schema(recipe: dict) -> dict:
    """Add schema to recipe data.

    More about recipe schema: https://schema.org/Recipe
    """

    schema = {
        '@context': 'https://schema.org',
        '@type': 'Recipe',
        'name': recipe['title']
    }

    if recipe['has_image']:
        schema['image'] = recipe['image']

    # servings = servings_schema(recipe)
    if servings_schema(recipe):
        schema['recipeYield'] = servings_schema(recipe)

    if recipe['scales'][0]['has_ingredients']:
        schema['recipeIngredient'] = []
        for ingredient in recipe['scales'][0]['ingredients']:
            schema['recipeIngredient'].append(ingredient['string'])

    recipe['schema_string'] = json.dumps(schema)
    return recipe


def servings_schema(recipe):
    """Returns schema string for servings. Empty string if no servings."""

    if recipe['scales'][0]['has_servings'] is False:
        return ''

    number = recipe['scales'][0]['servings']
    unit = 'serving' if number == 1 else 'servings'
    return f'{number} {unit}'


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
        Filename of the image file as a string, or empty string if no image.
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
    return utils.pipe(data,
                os.path.join(log_path, data['name']),
                set_homepage,
                set_href
                )


def set_homepage(collection):
    """Add homepage data to collection."""
    
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


def link_site(site: dict) -> dict:
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


def set_summary(site: dict) -> dict:
    """Adds summary data to site."""

    site['summary'] = {
        'recipes': summary_recipes(site),
        'collections': summary_collections(site),
        'ingredients': summary_ingredients(site)
        }
    return site


def summary_recipes(site):
    """Returns summary data for recipes."""

    recipes = []
    for recipe in site['recipes']:
        recipes.append({
            'title': recipe['title'],
            'collections': [c['name'] for c in recipe['collections']]
        })
    return recipes


def summary_collections(site):
    """Returns summary data for collections."""
    
    collections = []
    for collection in site['collections']:
        collections.append({
            'name': collection['name'],
            'recipes': [r['title'] for r in collection['recipes']]
        })
    return collections


def summary_ingredients(site):
    """Returns summary data for ingredients."""    

    ingredients = []
    for recipe in site['recipes']:
        for scale in recipe['scales']:
            for ingredient in scale['ingredients']:
                ingredients.append({
                    'recipe': recipe['title'],
                    'scale': scale['label'],
                    'ingredient': ingredient['string'],
                    'found_grocery': ingredient['has_grocery'],
                    'number_groceries': round(ingredient.get('grocery_number',
                                                             0),5)
                })
    return ingredients


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
        utils.make_qr_file(recipe['url'], os.path.join(recipe_dir, 'recipe-qr.png'))
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


def get_collection_dir(collection: dict, site_path: str) -> str:
    """Returns directory for a collection page."""

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
                              icon=icon)
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
                              icon=icon)
    write_file(content, file)


def make_summary_page(site: dict, page_path: str):
    """Create summary page for recipe site.

    Args:
        site: Site data as a dictionary.
        page_path: File path for summary page.
    """

    content = render_template('summary-page.html', 
                              recipes=site['summary']['recipes'], 
                              collections=site['summary']['collections'],
                              ingredients=site['summary']['ingredients'],
                              site_title=site_title())
    write_file(content, page_path)


if __name__ == "__main__":
    build()