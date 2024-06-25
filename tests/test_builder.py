import os
import sys

file_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.split(file_dir)[0]
jmr_dir = os.path.join(project_dir, 'jmrecipes')
sys.path.append(jmr_dir)

import buildsite


test_data = os.path.join(file_dir, 'data')


def test_pluralize_yield_unit():
    recipe_dir = os.path.join(test_data, 'test_yield_unit')
    recipe = buildsite.load_recipe(recipe_dir)
    assert recipe['scales'][0]['yield'][0]['unit'] == 'cup'
    assert recipe['scales'][1]['yield'][0]['unit'] == 'cup'
    assert recipe['scales'][2]['yield'][0]['unit'] == 'cups'


