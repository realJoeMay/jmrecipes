import unittest
import sys
import os
from fractions import Fraction

test_directory = os.path.dirname(os.path.abspath(__file__))
project_directory = os.path.split(test_directory)[0]
jmr_directory = os.path.join(project_directory, 'jmrecipes')

sys.path.append(jmr_directory)
from buildsite import load_recipe



test_data = os.path.join(test_directory, 'data')


class TestYieldUnit(unittest.TestCase):

    def test_positive_number(self):
        recipe_dir = os.path.join(test_data, 'test_yield_unit')
        recipe = load_recipe(recipe_dir)
        self.assertEqual(recipe['scales'][0]['yield'][0]['unit'], 'cup')
        self.assertEqual(recipe['scales'][1]['yield'][0]['unit'], 'cup')
        self.assertEqual(recipe['scales'][2]['yield'][0]['unit'], 'cups')


if __name__ == "__main__":
    unittest.main(verbosity=2)