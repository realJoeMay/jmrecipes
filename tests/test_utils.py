"""Unit tests for utility functions in src/utils/utils.py"""

from src.jmrecipes.utils import utils


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
