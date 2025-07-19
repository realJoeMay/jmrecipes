"""Unit tests for utility functions in src/utils/utils.py"""

from fractions import Fraction

from src.utils import utils


def test_aplit_amount_and_text():
    """Test splitting text into numeric quantity and remaining ingredient text."""

    assert utils.split_amount_and_text("1 cup") == (Fraction(1), "cup")
    assert utils.split_amount_and_text("2.5 cups") == (Fraction(5, 2), "cups")
    assert utils.split_amount_and_text("2 1/2 cups") == (Fraction(2.5), "cups")
    assert utils.split_amount_and_text("2 ½ cups") == (Fraction(2.5), "cups")
    assert utils.split_amount_and_text("2½ cups") == (Fraction(2.5), "cups")
    assert utils.split_amount_and_text("2.5 cubes beef boullion") == (
        Fraction(5, 2),
        "cubes beef boullion",
    )


def test_to_fraction():
    """Test converting various numeric types and strings to Fraction."""

    assert utils.to_fraction(1) == Fraction(1)
    assert utils.to_fraction(1.5) == Fraction(1.5)
    assert utils.to_fraction("2") == Fraction(2)
    assert utils.to_fraction("2.5") == Fraction(2.5)
    assert utils.to_fraction("2 1/2") == Fraction(2.5)
    assert utils.to_fraction("2 ½") == Fraction(2.5)
    assert utils.to_fraction("3½") == Fraction(3.5)


def test_fraction_to_string():
    """Test converting Fractions to string format (unicode and ASCII)."""

    assert utils.fraction_to_string(Fraction(1)) == "1"
    assert utils.fraction_to_string(Fraction(1), to_unicode=False) == "1"
    assert utils.fraction_to_string(Fraction(1.5)) == "1½"
    assert utils.fraction_to_string(Fraction(1.5), to_unicode=False) == "1 1/2"
    assert utils.fraction_to_string(Fraction(4, 3)) == "1⅓"
    assert utils.fraction_to_string(Fraction(4, 3), to_unicode=False) == "1 1/3"
    assert utils.fraction_to_string(Fraction(1, 3)) == "⅓"
    assert utils.fraction_to_string(Fraction(1, 3), to_unicode=False) == "1/3"


def test_is_youtube_url():
    """Test detection of valid YouTube URLs."""

    assert utils.is_youtube_url("https://www.youtube.com/watch?v=RmeM7WYB5Os") is True
    assert (
        utils.is_youtube_url("https://www.youtube.com/watch?v=RmeM7WYB5Os&t=100s")
        is True
    )
    assert utils.is_youtube_url("https://youtu.be/RmeM7WYB5Os") is True
    assert utils.is_youtube_url("https://youtu.be/RmeM7WYB5Os?t=2") is True
    assert (
        utils.is_youtube_url(
            "https://rumble.com/vlcvm7-strawberry-cake-amazing-short-cooking-video-recipe-and-food-hacks.html?e9s=rel_v2_ep"
        )
        is False
    )


def test_youtube_url_id():
    """Test extraction of YouTube video ID from various URL formats."""

    assert (
        utils.youtube_url_id("https://www.youtube.com/watch?v=RmeM7WYB5Os")
        == "RmeM7WYB5Os"
    )
    assert (
        utils.youtube_url_id("https://www.youtube.com/watch?v=RmeM7WYB5Os&t=100s")
        == "RmeM7WYB5Os"
    )
    assert utils.youtube_url_id("https://youtu.be/RmeM7WYB5Os") == "RmeM7WYB5Os"
    assert utils.youtube_url_id("https://youtu.be/RmeM7WYB5Os?t=2") == "RmeM7WYB5Os"
