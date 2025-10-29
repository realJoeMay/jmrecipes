"""Unit tests for parsing and processing recipe and site data."""

from pathlib import Path

from src.jmrecipes import build

file_dir = Path(__file__).resolve().parent
test_data = file_dir / "data"


def test_servings_from_yield_number():
    """Test parsing yield when it is expressed as a single number."""
    recipe_dir = test_data / "recipe_yield_as_number"
    recipe = build.load_recipe(recipe_dir)
    assert recipe["scales"][0]["servings"] == 2


def test_servings_from_yield_list():
    """Test parsing yield when it is expressed as a list of values."""
    recipe_dir = test_data / "recipe_yield_as_list"
    recipe = build.load_recipe(recipe_dir)
    assert recipe["scales"][0]["servings"] == 3


def test_explicit_ingredient_cost():
    """Test applying explicit cost values to ingredients across scales."""
    site_dir = test_data / "site_explicit_ingredient_cost"
    site = build.load_site(site_dir)
    assert site["recipes"][0]["scales"][0]["ingredients"][0]["cost"] == 100
    assert site["recipes"][0]["scales"][1]["ingredients"][0]["cost"] == 200


def test_pluralize_yield_unit():
    """Test correct pluralization of yield units across scales."""
    recipe_dir = test_data / "recipe_yield_unit"
    recipe = build.load_recipe(recipe_dir)
    assert recipe["scales"][0]["yield"][0]["unit"] == "cup"
    assert recipe["scales"][1]["yield"][0]["unit"] == "cup"
    assert recipe["scales"][2]["yield"][0]["unit"] == "cups"


def test_ingredient_grocery_amoount():
    """Test calculation of grocery quantities for various ingredients."""
    recipe_dir = test_data / "recipe_grocery_amount"
    recipe = build.load_recipe(recipe_dir)
    assert recipe["scales"][0]["ingredients"][0]["grocery_count"] == 0.5
    assert recipe["scales"][0]["ingredients"][1]["grocery_count"] == 0.5
    assert recipe["scales"][0]["ingredients"][2]["grocery_count"] == 2
    assert recipe["scales"][0]["ingredients"][3]["grocery_count"] == 3
    assert recipe["scales"][0]["ingredients"][4]["grocery_count"] == 0
