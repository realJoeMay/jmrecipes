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


def test_is_youtube_url():
    assert utils.is_youtube_url('https://www.youtube.com/watch?v=RmeM7WYB5Os') is True
    assert utils.is_youtube_url('https://www.youtube.com/watch?v=RmeM7WYB5Os&t=100s') is True
    assert utils.is_youtube_url('https://youtu.be/RmeM7WYB5Os') is True
    assert utils.is_youtube_url('https://youtu.be/RmeM7WYB5Os?t=2') is True
    assert utils.is_youtube_url('https://rumble.com/vlcvm7-strawberry-cake-amazing-short-cooking-video-recipe-and-food-hacks.html?e9s=rel_v2_ep') is False


def youtube_url_id():
    assert utils.youtube_url_id('https://www.youtube.com/watch?v=RmeM7WYB5Os') == 'RmeM7WYB5Os'
    assert utils.youtube_url_id('https://www.youtube.com/watch?v=RmeM7WYB5Os&t=100s') == 'RmeM7WYB5Os'
    assert utils.youtube_url_id('https://youtu.be/RmeM7WYB5Os') == 'RmeM7WYB5Os'
    assert utils.youtube_url_id('https://youtu.be/RmeM7WYB5Os?t=2') == 'RmeM7WYB5Os'
