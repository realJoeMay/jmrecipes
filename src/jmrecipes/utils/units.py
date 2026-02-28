"""Unit utilities for parsing, identifying, and converting units."""

import pandas as pd

from jmrecipes.paths import get_paths


def is_unit(text: str) -> bool:
    """Returns True if text is a single or plural unit."""

    if not text:
        return False

    _units = _load_units()

    single_units = set(_units["unit"])
    plural_units = set(_units["plural"])
    units = single_units.union(plural_units)
    return text in units


def is_weight(unit: str) -> bool:
    """Returns True if unit is a single or plural weight unit."""
    _units = _load_units()

    weights_df = _units[_units["type"] == "weight"]
    single_weights = set(weights_df["unit"])
    plural_weights = set(weights_df["plural"])
    weights = single_weights.union(plural_weights)
    return unit in weights


def is_volume(unit: str) -> bool:
    """Returns True if unit is a single or plural volume unit."""
    _units = _load_units()

    volume_df = _units[_units["type"] == "volume"]
    single_weights = set(volume_df["unit"])
    plural_weights = set(volume_df["plural"])
    volumes = single_weights.union(plural_weights)
    return unit in volumes


def is_equivalent(unit1: str, unit2: str) -> bool:
    """Determines if two units are the same.

    Units can be same by 3 ways:
    - unit1 and unit2 are same string
    - unit2 is plural of unit1
    - unit1 is plural of unit2
    """
    _units = _load_units()

    unit1 = unit1.lower()
    unit2 = unit2.lower()

    if unit1 == unit2:
        return True

    found1 = _units[(_units["unit"] == unit1) & (_units["plural"] == unit2)]
    found2 = _units[(_units["unit"] == unit2) & (_units["plural"] == unit1)]
    if found1.empty and found2.empty:
        return False
    else:
        return True


def to_standard(unit: str):
    """Returns a unit's conversion to standard."""
    _units = _load_units()

    unit_mask = _units["unit"] == unit
    plural_mask = _units["plural"] == unit
    standard_mask = _units["to_standard"] != 0
    matching_items = _units[(unit_mask | plural_mask) & standard_mask]
    if matching_items.empty:
        return 1
    matching_item = matching_items.iloc[0]
    return matching_item["to_standard"]


def numberize(unit: str, number: int | float) -> str:
    """Returns single or plural unit based on number."""

    return _plural(unit) if number > 1 else _single(unit)


def _plural(unit: str) -> str:
    """Returns plural version of a unit.

    If unit not found, return original unit.
    """

    if not unit:
        return unit

    _units = _load_units()

    matching_items = _units[_units["unit"] == unit]
    if matching_items.empty:
        return unit
    matching_item = matching_items.iloc[0]
    return matching_item["plural"]


def _single(unit: str) -> str:
    """Returns singular version of a unit.

    If unit not found, return original unit.
    """

    if not unit:
        return unit

    _units = _load_units()

    matching_items = _units[_units["plural"] == unit]
    if matching_items.empty:
        return unit
    matching_item = matching_items.iloc[0]
    return matching_item["unit"]


def _load_units() -> pd.DataFrame:
    """Loads list of units from file."""

    df = pd.read_csv(get_paths().data_dir / "units.csv")
    column_defaults = {"units": "", "plural": "", "type": "", "to_standard": 0}
    df.fillna(value=column_defaults, inplace=True)
    return df
