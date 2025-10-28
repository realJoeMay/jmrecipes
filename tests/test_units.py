"""Unit tests for utility functions in src/utils/units.py"""

import pytest

from src.jmrecipes.utils import units


@pytest.mark.parametrize(
    "unit",
    ["ml", "milliliter", "milliliters", "oz", "ounce", "ounces", "slices"],
)
def test_is_unit_valid_units(unit):
    """Test is_unit returns True for known units and plurals."""
    assert units.is_unit(unit) is True


@pytest.mark.parametrize("unit", ["not a real unit", "", "milk", "grams "])
def test_is_unit_invalid_units(unit):
    """Test is_unit returns False for unknown or malformed units."""
    assert units.is_unit(unit) is False


@pytest.mark.parametrize(
    "unit",
    ["g", "gram", "grams", "oz", "ounce", "ounces", "lb", "lbs", "pound", "pounds"],
)
def test_is_weight_true(unit):
    """Test is_weight returns True for weight units and their plurals."""
    assert units.is_weight(unit) is True


@pytest.mark.parametrize("unit", ["cup", "ml", "scoop", "notweight"])
def test_is_weight_false(unit):
    """Test is_weight returns False for non-weight units."""
    assert units.is_weight(unit) is False


@pytest.mark.parametrize(
    "unit", ["ml", "milliliter", "tsp", "tablespoon", "liter", "cups", "gallon"]
)
def test_is_volume_true(unit):
    """Test is_volume returns True for volume units and their plurals."""
    assert units.is_volume(unit) is True


@pytest.mark.parametrize("unit", ["g", "ounce", "stick", "burger"])
def test_is_volume_false(unit):
    """Test is_volume returns False for non-volume units."""
    assert units.is_volume(unit) is False


@pytest.mark.parametrize(
    "unit1, unit2",
    [
        ("cup", "cups"),
        ("cups", "cup"),
        ("pound", "pounds"),
        ("tsp", "tsp"),  # identical
    ],
)
def test_is_equivalent_true(unit1, unit2):
    """Test is_equivalent returns True for equivalent units."""
    assert units.is_equivalent(unit1, unit2) is True


@pytest.mark.parametrize(
    "unit1, unit2",
    [
        ("cup", "tsp"),
        ("grams", "cups"),
        ("burger", "loaf"),
        ("g", "oz"),
    ],
)
def test_is_equivalent_false(unit1, unit2):
    """Test is_equivalent returns False for unrelated units."""
    assert units.is_equivalent(unit1, unit2) is False


@pytest.mark.parametrize(
    "unit, expected",
    [
        ("ml", 1),
        ("liter", 1000),
        ("tsp", 4.92892),
        ("tbsp", 14.7868),
        ("cup", 236.588),
        ("oz", 28.3495),
        ("lb", 453.592),
        ("fakeunit", 1),
        ("slices", 1),  # not a convertible unit but should default to 1
    ],
)
def test_to_standard(unit, expected):
    """Test to_standard returns correct conversion factors or default 1."""
    assert units.to_standard(unit) == pytest.approx(expected)


@pytest.mark.parametrize(
    "unit, number, expected",
    [
        ("cup", 1, "cup"),
        ("cup", 2, "cups"),
        ("loaf", 1, "loaf"),
        ("loaf", 3, "loaves"),
        ("fakeunit", 1, "fakeunit"),
        ("fakeunit", 5, "fakeunit"),
    ],
)
def test_numberize(unit, number, expected):
    """Test numberize returns correct singular/plural form."""
    assert units.numberize(unit, number) == expected
