import unittest
import sys
import os

file_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.split(file_dir)[0]
jmr_dir = os.path.join(project_dir, 'jmrecipes')
sys.path.append(jmr_dir)

import buildsite
import utils


test_data = os.path.join(file_dir, 'data')


class TestYields(unittest.TestCase):

    def test_pluralize_yield_unit(self):
        recipe_dir = os.path.join(test_data, 'test_yield_unit')
        recipe = buildsite.load_recipe(recipe_dir)
        self.assertEqual(recipe['scales'][0]['yield'][0]['unit'], 'cup')
        self.assertEqual(recipe['scales'][1]['yield'][0]['unit'], 'cup')
        self.assertEqual(recipe['scales'][2]['yield'][0]['unit'], 'cups')


class TestUnits(unittest.TestCase):

    def test_numberize(self):
        self.assertEqual(utils.numberize('cup', 1), 'cup')
        self.assertEqual(utils.numberize('cups', 1), 'cup')
        self.assertEqual(utils.numberize('cup', 2), 'cups')
        self.assertEqual(utils.numberize('cups', 2), 'cups')
        self.assertEqual(utils.numberize('fake unit', 1), 'fake unit')
        self.assertEqual(utils.numberize('fake unit', 2), 'fake unit')


    def test_to_standard(self):
        self.assertEqual(utils.to_standard('ml'), 1)
        self.assertEqual(utils.to_standard('milliliter'), 1)
        self.assertEqual(utils.to_standard('milliliters'), 1)
        self.assertEqual(utils.to_standard('liter'), 1000)
        self.assertEqual(utils.to_standard('tsp'), 4.92892)
        self.assertEqual(utils.to_standard('g'), 1)
        self.assertEqual(utils.to_standard('grams'), 1)
        self.assertEqual(utils.to_standard('lbs'), 453.592)
        self.assertEqual(utils.to_standard('slice'), 1)
        self.assertEqual(utils.to_standard('slices'), 1)
        self.assertEqual(utils.to_standard('fake unit'), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)