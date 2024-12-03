import json
import yaml
from fractions import Fraction

from src.utils import to_fraction


def parse_recipe(file_path: str) -> dict:
    """Converts a recipe data file to a recipe dictionary.

    Args:
        filepath: Str path to recipe data file.

    Returns:
        Dict containing recipe data.
    """

    with open(file_path, 'r', encoding='utf8') as f:
        data = f.read()

    if file_path.endswith('.json'):
        return recipe_dict(json.loads(data))
    elif file_path.endswith('.yaml'):
        return recipe_dict(yaml.safe_load(data))

    raise ValueError('file is not a valid format')


def recipe_dict(data: dict) -> dict:
    """Restructures input dictionary to creates recipe dictionary.

    Args:
        data: Recipe input data as dictionary.

    Returns:
        Recipe data dictionary.
    """

    recipe = {}
    recipe['title'] = parse_title(data)
    recipe['subtitle'] = data.get('subtitle', '')
    recipe['times'] = parse_times(data)
    recipe['yield'] = parse_yield(data)
    recipe['ingredients'] = parse_ingredients(data)
    recipe['instructions'] = parse_instructions(data)
    recipe['scales'] = parse_scales(data) 
    recipe['videos'] = parse_videos(data)

    if 'description' in data:
        recipe['description'] = data['description']
    if 'cost' in data:
        recipe['explicit_cost'] = data['cost']
    if 'nutrition' in data:
        recipe['explicit_nutrition'] = parse_nutrition(data['nutrition'])
    if 'hide_cost' in data:
        recipe['hide_cost'] = bool(data['hide_cost'])
    if 'hide_nutrition' in data:
        recipe['hide_nutrition'] = bool(data['hide_nutrition'])
    if 'sources' in data:
        recipe['sources'] = parse_sources(data)
    if 'notes' in data:
        recipe['notes'] = parse_notes(data)

    return recipe


def parse_title(data):
    """Returns recipe title from input file."""

    if 'title' not in data:
        raise KeyError('Recipe must have a title')
    
    return data['title']


def parse_times(data):
    """Sets time data from input file."""

    times = []
    for time in data.get('times', []):
        times.append(parse_time(time))
    return times


def parse_time(time: dict) -> dict:
    """Formats a time entry."""

    if not isinstance(time, dict):
        raise TypeError('time must be a dict.')
    if 'name' not in time:
        raise KeyError('time must have a name.')
    if not isinstance(time['name'], str):
        raise TypeError('time name must be a string.')
    if 'time' not in time:
        raise KeyError('time must have a time.')
    if not isinstance(time['time'], (int, float)):
        raise TypeError(f'time time is a {type(time["time"])}, not a number.')
    if not isinstance(time.get('unit', ''), str):
        raise TypeError(f'time unit is a {type(time["unit"])}, not a string.')
    
    name = time['name']
    time_time = to_fraction(time['time'])
    time_data = {
        'name': name,
        'time': time_time,
        'unit': time.get('unit', '')
    }
    return time_data


def parse_yield(data):
    """Sets yield data from input file."""
# todo work on this
    if 'yield' not in data:
        return []
    
    yield_data = data['yield']
    
    if not isinstance(yield_data, (int, float, list)):
        raise TypeError('Yield data must be a number or a list.')

    if isinstance(yield_data, (int, float)):
        return [{'number': yield_data}]

    # yield is list
    yields = []
    for yield_item in data['yield']:
        yields.append(parse_yield_item(yield_item))
    return yields


def parse_yield_item(data):
    """Formats yield data from input file."""

    if 'number' not in data:
        raise KeyError('Yield data must have number field.')

    yielb = {'number': to_fraction(data['number'])}
    if 'unit' in data:
        yielb['unit'] = data['unit']
    if 'show_yield' in data:
        yielb['show_yield'] = bool(data['show_yield'])
    if 'show_serving_size' in data:
        yielb['show_serving_size'] = bool(data['show_serving_size'])
    
    return yielb


def parse_ingredients(data):
    """Sets ingredients data from input file."""

    ingredients = []
    for ingredient in data.get('ingredients', []):
        ingredients.append(parse_ingredient(ingredient))
    return ingredients


def parse_ingredient(data: dict) -> dict:
    """Formats ingredient data from input file."""

    ingredient = {
        'number': to_fraction(data.get('number', 0)),
        'unit': data.get('unit', ''),
        'item': data.get('item', ''),
        'descriptor': data.get('descriptor', ''),
        'display_number': to_fraction(data.get('display_number', 0)),
        'display_unit': data.get('display_unit', ''),
        'display_item': data.get('display_item', ''),
    }
    if 'list' in data:
        ingredient['list'] = data['list']
    if 'scale' in data:
        ingredient['scale'] = data['scale']
    if 'cost' in data:
        ingredient['explicit_cost'] = data['cost']
    if 'nutrition' in data:
        ingredient['explicit_nutrition'] = parse_nutrition(data['nutrition'])
    if 'recipe' in data:
        ingredient['recipe_slug'] = data['recipe']
    return ingredient


def parse_instructions(data):
    """Sets instructions data from input file."""

    instructions = []
    for step in data.get('instructions', []):
        instructions.append(parse_step(step))
    return instructions


def parse_step(data):
    """Formats instructions data from input file."""

    if not isinstance(data, (str, dict)):
        raise TypeError('Instructions step must be a string or dictionary.')
    
    if isinstance(data, dict) and 'text' not in data:
        raise KeyError('Instructions step must include "text" field.')

    if isinstance(data, str):
        return {'text': data}
        
    # data is dict with 'text'
    step = {'text': data['text']}
    if 'scale' in data:
        step['scale'] = data['scale']
    if 'list' in data:
        step['list'] = data['list']
    return step


def parse_scales(data):
    """Formats scale data from input file, including base scale."""

    scales = [{'multiplier': Fraction(1)}]
    for scale in data.get('scale', []):
        scales.append({'multiplier': read_multiplier(scale)})
    return scales


def read_multiplier(scale) -> Fraction:
    """Returns multiplier of a scale."""

    if not isinstance(scale, (int, float, str, dict)):
        raise TypeError('Scale must be a dict or number.')

    if isinstance(scale, dict):
        return to_fraction(scale['multiplier'])
    if isinstance(scale, (int, float, str)):
        return to_fraction(scale)
    

def parse_videos(data):
    """Returns videos from input data."""

    if 'video' not in data:
        return []
    if not isinstance(data['video'], list):
        raise TypeError('Videos data must be a list.')
    
    return [parse_video(d) for d in data['video']]


def parse_video(video_data):
    """Returns video from input data."""

    if not isinstance(video_data, dict):
        raise TypeError('Video data must be a dict.')
    if 'url' not in video_data:
        raise KeyError('Video must have url.')
    if not isinstance(video_data['url'], str):
        raise TypeError('Video url must be a str.')
    if 'list' in video_data and not isinstance(video_data['list'], str):
        raise TypeError('Video instruction_list must be a str.')
        
    video = {}
    video['url'] = video_data['url']
    if 'list' in video_data:
        video['list'] = video_data['list']
    return video


def parse_nutrition(nutrition):
    """Formats nutrition data from input file."""

    return {
        'calories': nutrition.get('calories', 0),
        'fat': nutrition.get('fat', 0),
        'protein': nutrition.get('protein', 0),
        'carbohydrates': nutrition.get('carbohydrates', 0),
    }


def parse_sources(data):
    """Returns sources data from input dictionary."""

    sources_data = data['sources']
    if not isinstance(sources_data, (list)):
        raise TypeError('Sources must be a list.')
    
    sources = []
    for source in sources_data:
        sources.append(parse_source(source))


    return sources


def parse_source(source):
    """Returns formatted source data from input file."""
    
    out = {}
    if 'name' in source and source['name']:
        out['name'] = source['name']
    if 'url' in source:
        out['url'] = source['url']
    return out


def parse_notes(data):
    """Returns notes data from input dictionary."""

    notes_data = data['notes']
    if not isinstance(notes_data, list):
        raise TypeError('Notes must be a list.')
    
    notes = []
    for note in notes_data:
        notes.append(parse_note(note))
    return notes


def parse_note(note_data):
    """Returns formatted note data from input file."""

    if not isinstance(note_data, dict):
        raise TypeError('Note must be a dictionary.')
    if 'text' not in note_data:
        raise KeyError('Note must have text.')
    
    note = {'text': note_data['text']}
    if 'scale' in note_data:
        note['scale'] = to_fraction(note_data['scale'])
    return note


def parse_collection(file_path: str) -> dict:
    """Converts a collection data file to a collection dictionary.

    Args:
        file_path: Str path to collection data file.

    Returns:
        Dict containing collection data.
    """

    with open(file_path, 'r', encoding='utf8') as f:
        data = f.read()

    if file_path.endswith('.json'):
        return json.loads(data)
    elif file_path.endswith('.yaml'):
        return yaml.safe_load(data)

    raise ValueError('file is not a valid format')

