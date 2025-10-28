"""Collection Builder Utilities"""

from jmrecipes.utils import utils


def set_collection_defaults(collection):
    """Sets default values for collection.

    Sets the following keys:
    - 'search_placeholder' (str)
    """

    if "search_placeholder" not in collection:
        collection["search_placeholder"] = utils.config("default", "search_placeholder")
    return collection


def set_homepage(collection):
    """Add homepage data to collection.

    Sets the following keys:
    - 'is_homepage' (bool)
    """

    collection["is_homepage"] = False
    if collection["url_path"] == "":
        collection["is_homepage"] = True
    return collection


def set_collection_url(collection):
    """Set href to a collection from a recipe page.

    Sets the following keys:
    - 'href' (str)
    - 'url' (str)
    """

    if collection["is_homepage"]:
        collection["href"] = ".."
    else:
        collection["href"] = f'../{collection["url_path"]}'

    url_path = "/" + collection["url_path"]
    collection["url"] = utils.make_url(path=url_path)
    feedback_name = collection["name"] + " (Collection)"
    collection["feedback_url"] = utils.feedback_url(feedback_name, collection["url"])

    return collection
