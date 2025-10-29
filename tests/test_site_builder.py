"""Unit tests for parsing and processing recipe and site data."""

from pathlib import Path
import pytest

from src.jmrecipes import build


file_dir = Path(__file__).resolve().parent
test_data = file_dir / "data"


def test_nested_recipe_quantity():
    """Test that nested recipe quantities are correctly resolved."""
    site_dir = test_data / "site_nested_recipe_quantity"
    site = build.load_site(site_dir)
    qty_volume = site["recipes"][-1]["scales"][0]["ingredients"][0]["recipe_quantity"]
    qty_weight = site["recipes"][-1]["scales"][0]["ingredients"][1]["recipe_quantity"]
    qty_units = site["recipes"][-1]["scales"][0]["ingredients"][2]["recipe_quantity"]
    assert qty_volume == 12
    assert qty_weight == pytest.approx(6)
    assert qty_units == 2


def test_nested_recipe_loop_error():
    """Test that a cyclic reference in nested recipes raises a ValueError."""
    site_dir = test_data / "site_nested_recipe_loop_error"
    with pytest.raises(ValueError, match="Cyclic recipe reference found"):
        build.load_site(site_dir)
