"""Various utilities."""

from configparser import ConfigParser
from fractions import Fraction
import json
import os
from pathlib import Path
import shutil
from urllib.parse import urlparse, urlunparse, urlencode, parse_qs
from typing import Union
import re


# Directories
utils_directory = os.path.dirname(os.path.abspath(__file__))
jmr_directory = os.path.split(utils_directory)[0]
src_directory = os.path.split(jmr_directory)[0]
project_directory = os.path.split(src_directory)[0]
builds_directory = os.path.join(project_directory, "builds")
data_directory = os.path.join(project_directory, "data")
assets_directory = os.path.join(data_directory, "assets")


# Folders and files
def create_dir(path):
    """Create a folder."""

    if not os.path.exists(path):
        os.mkdir(path)


def make_empty_dir(path):
    """Create a folder.

    Empty folder if already exists.
    """

    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)


def write_file(content: str, path: Path):
    """Save content to a text file."""

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def write_json_file(data: dict, path: str):
    """Save dictionary data to a JSON file.

    Args:
        data: Dictionary of data to write.
        path: File path
    """

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, cls=JMREncoder)


class JMREncoder(json.JSONEncoder):
    """Extends JSONEncoder to work with Fraction objects.

    More info:
    https://dev.to/kfuquay/extending-pythons-json-encoder-7k0
    """

    def default(self, o):
        if isinstance(o, Fraction):
            o = str(o) + " <Fraction>"
            return o

        # Default behavior for all other types
        return super().default(o)


# Pipe
def pipe(data: dict, log_path: Path | None, *funcs) -> dict:
    """Pipe data through a sequence of functions.

    Optionally saves data after each function in log files. Saves no log
    if log_path is None.
    """

    has_log = log_path is not None

    if has_log:
        create_dir(log_path)
        log_file_path_0 = os.path.join(log_path, "0_start.json")
        write_json_file(data, log_file_path_0)

    for i, func in enumerate(funcs, 1):
        data = func(data)
        if has_log:
            log_file_path = os.path.join(log_path, f"{i}_{func.__name__}.json")
            write_json_file(data, log_file_path)

    return data


# Config file
def config(section: str, name: str, as_boolean: bool = False) -> str | bool:
    """Read from config file."""

    config_path = os.path.join(data_directory, "config.ini")
    parser = ConfigParser()
    parser.read(config_path)
    if as_boolean:
        return parser.getboolean(section, name)
    return parser.get(section, name)


def site_title() -> str:
    """Read site title from config file."""

    return str(config("site", "title"))


def format_currency(cost: Union[int, float]) -> str:
    """Formats a cost value as a currency string.

    This function converts a numeric cost value into a string
    formatted as currency. The cost is rounded to two decimal places
    and prefixed with a dollar sign.

    Args:
        cost (int | float): The numeric value to format.

    Returns:
        str: A string formatted like "$1.23".
    """
    return f"${float(cost):.2f}"


# URLs
def make_url(**kwargs) -> str:
    """Constructs a URL from components passed as keyword arguments.

    Keyword Args:
        scheme (str): URL scheme (default: 'https')
        domain (str): Domain name (default: from config file)
        path (str): URL path (default: '')
        params (str): URL parameters (default: '')
        query (dict): Query parameters as a dictionary (default: None)
        fragment (str): URL fragment (default: '')

    Returns:
        str: A fully constructed URL string.
    """

    scheme = kwargs.get("scheme", "https")
    domain = kwargs.get("domain", config("site", "domain"))
    path = kwargs.get("path", "")
    params = kwargs.get("params", "")
    fragment = kwargs.get("fragment", "")

    query_dict = kwargs.get("query")
    query = urlencode(query_dict) if query_dict else ""

    return urlunparse([scheme, domain, path, params, query, fragment])


def feedback_url(page_name: str, source_url: str) -> str:
    """Create feedback url with prefilled values."""

    components = urlparse(str(config("feedback", "url")))
    query = {"prefill_page": page_name, "prefill_source_url": source_url}
    return make_url(domain=components[1], path=components[2], query=query)


def sluggify(name: str) -> str:
    """Converts a string to a URL-friendly slug.

    The resulting slug:
        - Uses lowercase ASCII letters and digits
        - Replaces spaces and underscores with dashes
        - Removes non-alphanumeric characters (excluding dashes)
        - Condenses multiple dashes into one

    Parameters:
        name (str): The input string to convert.

    Returns:
        str: A URL-safe slug.
    """

    slug = name.lower()
    slug = re.sub(r"[ _]+", "-", slug)  # Replace spaces and underscores with dashes
    slug = re.sub(r"[^a-z0-9\-]", "", slug)  # Remove invalid characters
    slug = re.sub(r"-{2,}", "-", slug)  # Replace multiple dashes with one
    slug = slug.strip("-")  # Strip leading/trailing dashes
    return slug


def is_youtube_url(url: str) -> bool:
    """Determines whether the given URL is a YouTube video link."""

    return _is_youtube_full_url(url) or _is_youtube_short_url(url)


def youtube_url_id(url: str) -> str:
    """Returns youtube video ID from url."""

    if _is_youtube_full_url(url):
        return _youtube_full_url_id(url)
    elif _is_youtube_short_url(url):
        return _youtube_short_url_id(url)
    raise ValueError(f"Cannot get youtube video ID from url: {url}")


def youtube_embed_url(video_id: str) -> str:
    """Returns embed url for a youtube video."""

    return f'<iframe src="https://www.youtube.com/embed/{video_id}" allowfullscreen></iframe>'


def _is_youtube_full_url(url: str) -> bool:

    return "youtube.com/watch" in url


def _is_youtube_short_url(url: str) -> bool:

    return "youtu.be/" in url


def _youtube_full_url_id(url: str) -> str:
    """Returns youtube video ID from full url."""

    parsed_url = urlparse(url)
    query_string = parsed_url.query
    query_params = parse_qs(query_string)
    return query_params["v"][0]


def _youtube_short_url_id(url: str) -> str:
    """Returns youtube video ID from short url."""

    parsed_url = urlparse(url)
    path = parsed_url.path
    return path.strip("/")
