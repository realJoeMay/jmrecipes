"""Unit tests for parsing and processing recipe and site data."""

import os
import pytest

from src import build

file_dir = os.path.dirname(os.path.abspath(__file__))
test_data = os.path.join(file_dir, "data")


def test_parse_yield_as_number():
    """Test parsing yield when it is expressed as a single number."""
    recipe_dir = os.path.join(test_data, "recipe_yield_as_number")
    recipe = build.load_recipe(recipe_dir)
    assert recipe["scales"][0]["servings"] == 2


def test_parse_yield_as_list():
    """Test parsing yield when it is expressed as a list of values."""
    recipe_dir = os.path.join(test_data, "recipe_yield_as_list")
    recipe = build.load_recipe(recipe_dir)
    assert recipe["scales"][0]["servings"] == 3


def test_explicit_ingredient_cost():
    """Test applying explicit cost values to ingredients across scales."""
    site_dir = os.path.join(test_data, "site_explicit_ingredient_cost")
    site = build.load_site(site_dir)
    assert site["recipes"][0]["scales"][0]["ingredients"][0]["cost"] == 100
    assert site["recipes"][0]["scales"][1]["ingredients"][0]["cost"] == 200


def test_pluralize_yield_unit():
    """Test correct pluralization of yield units across scales."""
    recipe_dir = os.path.join(test_data, "recipe_yield_unit")
    recipe = build.load_recipe(recipe_dir)
    assert recipe["scales"][0]["yield"][0]["unit"] == "cup"
    assert recipe["scales"][1]["yield"][0]["unit"] == "cup"
    assert recipe["scales"][2]["yield"][0]["unit"] == "cups"


def test_ingredient_grocery_amoount():
    """Test calculation of grocery quantities for various ingredients."""
    recipe_dir = os.path.join(test_data, "recipe_grocery_amount")
    recipe = build.load_recipe(recipe_dir)
    assert recipe["scales"][0]["ingredients"][0]["grocery_count"] == 0.5
    assert recipe["scales"][0]["ingredients"][1]["grocery_count"] == 0.5
    assert recipe["scales"][0]["ingredients"][2]["grocery_count"] == 2
    assert recipe["scales"][0]["ingredients"][3]["grocery_count"] == 3
    assert recipe["scales"][0]["ingredients"][4]["grocery_count"] == 0


def test_nested_recipe_quantity():
    """Test that nested recipe quantities are correctly resolved."""
    site_dir = os.path.join(test_data, "site_nested_recipe_quantity")
    site = build.load_site(site_dir)
    qty_volume = site["recipes"][-1]["scales"][0]["ingredients"][0]["recipe_quantity"]
    qty_weight = site["recipes"][-1]["scales"][0]["ingredients"][1]["recipe_quantity"]
    qty_units = site["recipes"][-1]["scales"][0]["ingredients"][2]["recipe_quantity"]
    assert qty_volume == 12
    assert qty_weight == pytest.approx(6)
    assert qty_units == 2


def test_nested_recipe_loop_error():
    """Test that a cyclic reference in nested recipes raises a ValueError."""
    site_dir = os.path.join(test_data, "site_nested_recipe_loop_error")
    with pytest.raises(ValueError, match="Cyclic recipe reference found"):
        build.load_site(site_dir)
