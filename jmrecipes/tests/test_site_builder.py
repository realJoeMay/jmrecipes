"""Unit tests for parsing and processing recipe and site data."""

import os
import pytest

from src import build

file_dir = os.path.dirname(os.path.abspath(__file__))
test_data = os.path.join(file_dir, "data")


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
