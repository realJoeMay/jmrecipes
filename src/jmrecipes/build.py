"""Recipe Site Builder"""

import datetime
import os
import shutil
from typing import Optional

from jmrecipes.builder import from_file
from jmrecipes.builder import recipe_builder
from jmrecipes.builder import collection_builder
from jmrecipes.builder import site_builder
from jmrecipes.utils import utils
from jmrecipes.utils import template
from jmrecipes.utils import qr


def build():
    """Loads site data and creates a recipe website.

    Build the recipe website by loading data, generating site
    structure, rendering HTML pages, and saving the result.

    Output Structure:
        builds/
        └── latest/
            ├── web/       - HTML files for deployment
            ├── local/     - HTML files for local usage
            └── build-log/ - Logs for recipe and site processing

    Returns:
        None
    """

    timestamp = datetime.datetime.now()

    latest_folder = os.path.join(utils.builds_directory, "latest")
    site_web = os.path.join(latest_folder, "web")
    site_local = os.path.join(latest_folder, "local")
    log = os.path.join(latest_folder, "build-log")

    utils.create_dir(utils.builds_directory)
    utils.make_empty_dir(latest_folder)
    utils.create_dir(log)

    site = load_site(utils.data_directory, log)
    build_site(site, site_web, timestamp, verbose=True)
    build_site(site, site_local, timestamp, local=True)

    timestamp_folder = os.path.join(
        utils.builds_directory, timestamp.strftime("%Y-%m-%d %H-%M-%S")
    )
    shutil.copytree(latest_folder, timestamp_folder)
    print("Build complete")


def load_site(data_path, log_path=None) -> dict:
    """Loads site data from directory.

    Args:
        data_path: Directory with site data files.
        log: Directory to save site level log files.

    Returns:
        Site data as a dictionary.
        {'recipes': [r1, r2, r3],
         'collection': [c1, c2]}
    """

    recipes_path = os.path.join(data_path, "recipes")
    collections_path = os.path.join(data_path, "collections")
    has_log = log_path is not None

    if has_log:
        recipes_log_path = os.path.join(log_path, "recipes")
        collections_log_path = os.path.join(log_path, "collections")
        recipes = load_recipes(recipes_path, log_path=recipes_log_path)
        collections = load_collections(collections_path, log_path=collections_log_path)
        pipe_log_path = log_path
    else:
        recipes = load_recipes(recipes_path)
        collections = load_collections(collections_path)
        pipe_log_path = ""

    site = {"recipes": recipes, "collections": collections}
    return utils.pipe(
        site,
        pipe_log_path,
        site_builder.set_child_recipe_links,
        site_builder.set_recipes_used_in,
        site_builder.set_ingredient_as_recipe_quantities,
        site_builder.set_costs,
        site_builder.set_costs_per_serving,
        site_builder.set_cost_strings,
        site_builder.set_nutrition,
        site_builder.set_display_nutrition,
        site_builder.set_ingredient_details,
        site_builder.set_description_areas,
        site_builder.set_ingredient_lists,
        site_builder.link_recipes_collections,
        site_builder.set_search_values,
        site_builder.set_summary,
    )


def load_recipes(recipes_path: str, log_path: Optional[str] = None) -> list:
    """Loads data for recipes.

    Args:
        recipes_path: Directory that contains recipe data folders.
        log: Directory to save recipes level log files.

    Returns:
        Recipes data as a list of dictionaries, one for each recipe.
    """

    has_log = log_path is not None
    if has_log:
        utils.create_dir(log_path)

    recipes = []
    for folder in os.listdir(recipes_path):
        recipe_path = os.path.join(recipes_path, folder)

        if has_log:
            recipe_log_path = os.path.join(log_path, folder)
            utils.create_dir(recipe_log_path)
            recipes.append(load_recipe(recipe_path, log_path))
        else:
            recipes.append(load_recipe(recipe_path))

    return recipes


def load_recipe(recipe_path: str, log_path=None) -> dict:
    """Generates recipe data from a folder.

    Extracts data from folder, including the data file, image, and folder name
    as url_slug. Then, process the data to include everything needed for site.

    Args:
        recipe_path: Directory for a recipe's data.
        log_path: Directory to save recipe pipe log files.

    Returns:
        Recipes data as a dictionary.
    """

    file_name = recipe_file(recipe_path)
    file_path = os.path.join(recipe_path, file_name)
    file_data = from_file.recipe(file_path)
    file_data["folder_name"] = os.path.basename(recipe_path)

    recipe = {}
    recipe["file"] = file_data

    image = recipe_image(recipe_path)
    if image:
        recipe["image"] = image
        recipe["image_path"] = os.path.join(recipe_path, image)

    if log_path is None:
        log_path = ""
    else:
        log_path = os.path.join(log_path, file_data["folder_name"])

    return utils.pipe(
        recipe,
        log_path,
        recipe_builder.standardize_yields,
        recipe_builder.standardize_instructions,
        recipe_builder.standardize_ingredients,
        recipe_builder.set_title,
        recipe_builder.set_url,
        recipe_builder.set_description,
        recipe_builder.set_image,
        recipe_builder.set_scales,
        recipe_builder.set_times,
        recipe_builder.scale_yields,
        recipe_builder.set_servings,
        recipe_builder.set_visible_yields,
        recipe_builder.set_visible_serving_sizes,
        recipe_builder.set_copy_ingredients_sublabel,
        recipe_builder.set_ingredients_type,
        recipe_builder.scale_ingredients,
        recipe_builder.set_ingredient_outputs,
        recipe_builder.lookup_groceries,
        recipe_builder.set_instructions,
        recipe_builder.set_sources,
        recipe_builder.set_notes,
        recipe_builder.set_videos,
        recipe_builder.set_schema,
        recipe_builder.set_search_targets,
        recipe_builder.set_special_cases,
    )


def recipe_file(recipe_path: str) -> str:
    """Finds a recipe data file inside a folder.

    Args:
        recipe_path: A directory to search in.

    Returns:
        Filename of the recipe data file as a string.

    Raises:
        OSError: If no recipe data file was found.
    """

    for file in os.listdir(recipe_path):
        if file.endswith((".json", ".yaml")):
            return file
    raise OSError(f"Recipe data file not found in {dir}")


def recipe_image(recipe_path: str) -> str:
    """Finds a recipe image file inside a folder.

    Args:
        recipe_path: A directory to search in.

    Returns:
        Filename of the image file as a string, or empty string if no image.
    """

    for file in os.listdir(recipe_path):
        if file.endswith((".jpg", ".jpeg", "png")):
            return file
    return ""


def load_collections(collections_path: str, log_path: Optional[str] = None) -> list:
    """Generates data for collections.

    Args:
        collections_path: Directory that contains collections data files.
        log_path: Directory to save collection level log files.

    Returns:
        Collections data as a list of dictionaries.
    """

    has_log = log_path is not None
    if has_log:
        utils.create_dir(log_path)

    collections = []
    for file in os.listdir(collections_path):
        file_path = os.path.join(collections_path, file)

        if has_log:
            collection_log_path = os.path.join(log_path, file)
            collections.append(load_collection(file_path, collection_log_path))
        else:
            collections.append(load_collection(file_path))
    return collections


def load_collection(file_path, log_path=None) -> dict:
    """Generates data for a collection.

    Args:
        file_path: Directory that contains collections data files.
        log_path: Directory to save collection pipe log files.

    Returns:
        Collection data as a dictionary.
    """

    has_log = log_path is not None
    if not has_log:
        log_path = ""

    data = from_file.collection(file_path)
    return utils.pipe(
        data,
        log_path,
        collection_builder.set_collection_defaults,
        collection_builder.set_homepage,
        collection_builder.set_collection_url,
    )


def build_site(
    site: dict, site_path: str, timestamp: datetime.datetime, local=False, verbose=False
) -> None:
    """Builds a recipe site using site data.

    Args:
        site: Site data as a dictionary.
        site_path: Path to build the site inside.
        local: Builds local version if true, web version otherwise. Defaults is False.
    """

    utils.make_empty_dir(site_path)

    for recipe in site["recipes"]:
        recipe_dir = os.path.join(site_path, recipe["url_slug"])
        make_recipe_page(recipe, recipe_dir, local)
        qr.create(recipe["url"], os.path.join(recipe_dir, "recipe-qr.png"))
        make_print_page(recipe, os.path.join(recipe_dir, "p"), local)
        if recipe["has_image"]:
            shutil.copyfile(
                recipe["image_path"], os.path.join(recipe_dir, recipe["image"])
            )
        if verbose:
            print(f'Recipe: {recipe["title"]}')

    for collection in site["collections"]:
        collection_dir = get_collection_dir(collection, site_path)
        make_collection_page(collection, collection_dir, local)
        if verbose:
            print(f'Collection: {collection["name"]}')

    error_path = os.path.join(site_path, "404.html")
    make_404_page(error_path)

    summary_path = os.path.join(site_path, "summary.html")
    make_summary_page(site, timestamp, local, summary_path)

    shutil.copyfile(
        os.path.join(utils.assets_directory, "icon.png"),
        os.path.join(site_path, "icon.png"),
    )
    shutil.copyfile(
        os.path.join(utils.assets_directory, "default_720x540.jpg"),
        os.path.join(site_path, "default.jpg"),
    )
    # shutil.copytree(utils.data_directory, os.path.join(site_path, "data"))


def get_collection_dir(collection: dict, site_path: str) -> str:
    """Returns site directory for a collection page."""

    if collection["is_homepage"]:
        return site_path
    return os.path.join(site_path, collection["url_path"])


def make_recipe_page(recipe: dict, output_dir: str, local: bool) -> None:
    """Create index.html file for recipe page.

    Args:
        recipe: Recipe data as a dictionary.
        output_dir: Path to build the page inside.
        local: Builds local version if true, web version otherwise.
    """

    utils.create_dir(output_dir)
    file = os.path.join(output_dir, "index.html")
    content = template.render(
        "recipe-page.html",
        r=recipe,
        icon=template.icons,
        site_title=utils.site_title(),
        is_local=local,
    )
    utils.write_file(content, file)


def make_print_page(recipe: dict, output_dir: str, local: bool) -> None:
    """Create index.html file for recipe print page.

    Args:
        recipe: Recipe data as a dictionary.
        output_dir: Path to build the page inside.
        local: Builds local version if true, web version otherwise.
    """

    utils.create_dir(output_dir)
    file = os.path.join(output_dir, "index.html")
    content = template.render(
        "print-page.html",
        r=recipe,
        is_local=local,
        site_title=utils.site_title(),
        icon=template.icons,
    )
    utils.write_file(content, file)


def make_collection_page(collection: dict, output_dir: str, local: bool) -> None:
    """Create index.html file for collection page.

    Args:
        collection: Collection data as a dictionary.
        output_dir: Path to build the page inside.
        local: Builds local version if true, web version otherwise.
    """

    utils.create_dir(output_dir)
    file = os.path.join(output_dir, "index.html")
    content = template.render(
        "collection.html",
        c=collection,
        is_local=local,
        site_title=utils.site_title(),
        icon=template.icons,
    )
    utils.write_file(content, file)


def make_summary_page(
    site: dict, timestamp: datetime.datetime, local: bool, page_path: str
) -> None:
    """Create summary page for recipe site.

    Args:
        site: Site data as a dictionary.
        page_path: File path for summary page.
    """

    content = template.render(
        "summary-page.html",
        timestamp_str=timestamp.strftime("%B %d, %Y").replace(" 0", " "),
        recipes=site["summary"]["recipes"],
        collections=site["summary"]["collections"],
        ingredients=site["summary"]["ingredients"],
        groceries=site["summary"]["groceries"],
        site_title=utils.site_title(),
        is_local=local,
    )
    utils.write_file(content, page_path)


def make_404_page(page_path: str) -> None:
    """Create 404 page for recipe site.

    Args:
        page_path: File path for 404 page.
    """

    content = template.render("404.html", site_title=utils.site_title())
    utils.write_file(content, page_path)
