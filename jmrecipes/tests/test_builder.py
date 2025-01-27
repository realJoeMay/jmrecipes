import os
import sys
import pytest

file_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.split(file_dir)[0]
sys.path.append(project_dir)
import src.builder as builder


test_data = os.path.join(file_dir, 'data')

def test_parse_yield_as_number():
    recipe_dir = os.path.join(test_data, 'recipe_yield_as_number')
    recipe = builder.load_recipe(recipe_dir)
    assert recipe['scales'][0]['servings'] == 2


def test_parse_yield_as_list():
    recipe_dir = os.path.join(test_data, 'recipe_yield_as_list')
    recipe = builder.load_recipe(recipe_dir)
    assert recipe['scales'][0]['servings'] == 3


def test_explicit_ingredient_cost():
    site_dir = os.path.join(test_data, 'site_explicit_ingredient_cost')
    site = builder.load_site(site_dir)
    assert site['recipes'][0]['scales'][0]['ingredients'][0]['cost'] == 100
    assert site['recipes'][0]['scales'][1]['ingredients'][0]['cost'] == 200


def test_pluralize_yield_unit():
    recipe_dir = os.path.join(test_data, 'recipe_yield_unit')
    recipe = builder.load_recipe(recipe_dir)
    assert recipe['scales'][0]['yield'][0]['unit'] == 'cup'
    assert recipe['scales'][1]['yield'][0]['unit'] == 'cup'
    assert recipe['scales'][2]['yield'][0]['unit'] == 'cups'


def test_ingredient_grocery_amoount():
    recipe_dir = os.path.join(test_data, 'recipe_grocery_amount')
    recipe = builder.load_recipe(recipe_dir)
    assert recipe['scales'][0]['ingredients'][0]['grocery_count'] == 0.5
    assert recipe['scales'][0]['ingredients'][1]['grocery_count'] == 0.5
    assert recipe['scales'][0]['ingredients'][2]['grocery_count'] == 2
    assert recipe['scales'][0]['ingredients'][3]['grocery_count'] == 3
    assert recipe['scales'][0]['ingredients'][4]['grocery_count'] == 0


def test_nested_recipe_quantity():
    site_dir = os.path.join(test_data, 'site_nested_recipe_quantity')
    site = builder.load_site(site_dir)
    qty_volume = site['recipes'][-1]['scales'][0]['ingredients'][0]['recipe_quantity']
    qty_weight = site['recipes'][-1]['scales'][0]['ingredients'][1]['recipe_quantity']
    qty_units = site['recipes'][-1]['scales'][0]['ingredients'][2]['recipe_quantity']
    assert qty_volume == 12
    assert qty_weight == pytest.approx(6)
    assert qty_units == 2


def test_nested_recipe_loop_error():
    site_dir = os.path.join(test_data, 'site_nested_recipe_loop_error')
    with pytest.raises(ValueError, match='Cyclic recipe reference found'):
        site = builder.load_site(site_dir)


