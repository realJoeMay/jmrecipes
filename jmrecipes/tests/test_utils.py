import os
import sys

file_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.split(file_dir)[0]
sys.path.append(project_dir)
import src.utils as utils


def test_unit_numberize():
    assert utils.numberize('cup', 1) == 'cup'
    assert utils.numberize('cups', 1) == 'cup'
    assert utils.numberize('cup', 2) == 'cups'
    assert utils.numberize('cups', 2) == 'cups'
    assert utils.numberize('fake unit', 1) == 'fake unit'
    assert utils.numberize('fake unit', 2) == 'fake unit'


def test_unit_to_standard():
    assert utils.to_standard('ml') == 1
    assert utils.to_standard('milliliter') == 1
    assert utils.to_standard('milliliters') == 1
    assert utils.to_standard('liter') == 1000
    assert utils.to_standard('tsp') == 4.92892
    assert utils.to_standard('g') == 1
    assert utils.to_standard('grams') == 1
    assert utils.to_standard('lbs') == 453.592
    assert utils.to_standard('slice') == 1
    assert utils.to_standard('slices') == 1
    assert utils.to_standard('fake unit') == 1