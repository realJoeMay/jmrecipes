"""Recipe Site Builder"""

import datetime
import os
from pathlib import Path
import shutil
from typing import Optional

from jmrecipes.builder import from_file
from jmrecipes.builder import recipe_builder
from jmrecipes.builder import collection_builder
from jmrecipes.builder import site_builder
from jmrecipes.paths import PathConfig
from jmrecipes.utils import utils
from jmrecipes.utils import template
from jmrecipes.utils import qr


def build():
    """Loads site data and creates a recipe website."""

    timestamp = datetime.datetime.now()

    paths = PathConfig().ensure()
    latest_folder = paths.builds_dir / "latest"
    site_web = latest_folder / "web"
    site_local = latest_folder / "local"
    site_log_path = latest_folder / "build-log"

    utils.create_dir(paths.builds_dir)
    utils.make_empty_dir(latest_folder)
    utils.create_dir(site_log_path)

    site = load_site(paths.data_dir, site_log_path)
    build_site(site, site_web, timestamp, verbose=True)
    build_site(site, site_local, timestamp, local=True)

    timestamp_folder = paths.builds_dir / timestamp.strftime("%Y-%m-%d %H-%M-%S")
    shutil.copytree(latest_folder, timestamp_folder)
    print("Build complete")


def load_site(data_path: Path, site_log_path: Optional[Path] = None) -> dict:
    """Loads site data from directory.

    Args:
        data_path: Directory with site data files.
        log: Directory to save site level log files.

    Returns:
        Site data as a dictionary.
        {'recipes': [r1, r2, r3],
         'collection': [c1, c2]}
    """

    recipes_data_path = data_path / "recipes"
    collections_data_path = data_path / "collections"

    if site_log_path is not None:
        recipes_log_path = site_log_path / "recipes"
        collections_log_path = site_log_path / "collections"
        recipes = load_recipes(recipes_data_path, recipes_log_path=recipes_log_path)
        collections = load_collections(
            collections_data_path, collections_log_path=collections_log_path
        )
    else:
        recipes = load_recipes(recipes_data_path)
        collections = load_collections(collections_data_path)

    site = {"recipes": recipes, "collections": collections}
    return utils.pipe(
        site,
        site_log_path,
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


def load_recipes(recipes_path: Path, recipes_log_path: Optional[Path] = None) -> list:
    """Loads data for recipes.

    Args:
        recipes_path: Directory that contains recipe data folders.
        log: Directory to save recipes level log files.

    Returns:
        Recipes data as a list of dictionaries, one for each recipe.
    """

    has_log = recipes_log_path is not None
    if has_log:
        utils.create_dir(recipes_log_path)

    recipes = []
    for recipe_folder in os.listdir(recipes_path):
        recipe_path = recipes_path / recipe_folder
        recipe_log_path = None
        if has_log:
            recipe_log_path = recipes_log_path / recipe_folder
        recipes.append(load_recipe(recipe_path, recipe_log_path))
    return recipes


def load_recipe(recipe_path: Path, recipe_log_path: Optional[Path] = None) -> dict:
    """Generates recipe data from a folder.

    Extracts data from folder, including the data file, image, and folder name
    as url_slug. Then, process the data to include everything needed for site.

    Args:
        recipe_path: Directory for a recipe's data.
        recipe_log_path: Directory to save recipe pipe log files.

    Returns:
        Recipes data as a dictionary.
    """

    file_name = recipe_file(recipe_path)
    file_path = recipe_path / file_name
    file_data = from_file.recipe(file_path)
    file_data["folder_name"] = os.path.basename(recipe_path)

    recipe = {}
    recipe["file"] = file_data

    image = recipe_image(recipe_path)
    if image:
        recipe["image"] = image
        recipe["image_path"] = os.path.join(recipe_path, image)

    if recipe_log_path is not None:
        utils.create_dir(recipe_log_path)

    return utils.pipe(
        recipe,
        recipe_log_path,
        recipe_builder.normalize_yields,
        recipe_builder.normalize_instructions,
        recipe_builder.normalize_ingredients,
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
        recipe_builder.lookup_groceries,
        recipe_builder.set_ingredient_outputs,
        recipe_builder.set_instructions,
        recipe_builder.set_sources,
        recipe_builder.set_notes,
        recipe_builder.set_videos,
        recipe_builder.set_schema,
        recipe_builder.set_search_targets,
        recipe_builder.set_special_cases,
    )


def recipe_file(recipe_path: Path) -> str:
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


def recipe_image(recipe_path: Path) -> str:
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


def load_collections(
    collections_path: Path, collections_log_path: Optional[Path] = None
) -> list:
    """Generates data for collections.

    Args:
        collections_path: Directory that contains collections data files.
        collections_log_path: Directory to save collection log files.

    Returns:
        Collections data as a list of dictionaries.
    """

    if not collections_path.exists():
        return []

    has_log = collections_log_path is not None
    if has_log:
        utils.create_dir(collections_log_path)

    collections = []
    for collection_file in os.listdir(collections_path):
        collection_file_path = collections_path / collection_file

        if has_log:
            collection_log_path = collections_log_path / collection_file
            collections.append(
                load_collection(collection_file_path, collection_log_path)
            )
        else:
            collections.append(load_collection(collection_file_path))
    return collections


def load_collection(
    collection_file_path: Path, collection_log_path: Optional[Path] = None
) -> dict:
    """Generates data for a collection.

    Args:
        file_path: Directory that contains collections data files.
        collection_log_path: Directory to save collection pipe log files.

    Returns:
        Collection data as a dictionary.
    """

    return utils.pipe(
        from_file.collection(collection_file_path),
        collection_log_path,
        collection_builder.set_collection_defaults,
        collection_builder.set_homepage,
        collection_builder.set_collection_url,
    )


def build_site(
    site: dict,
    site_path: Path,
    timestamp: datetime.datetime,
    local=False,
    verbose=False,
) -> None:
    """Builds a recipe site using site data.

    Args:
        site: Site data as a dictionary.
        site_path: Path to build the site inside.
        local: Builds local version if true, web version otherwise. Defaults is False.
    """

    utils.make_empty_dir(site_path)

    for recipe in site["recipes"]:
        recipe_dir = site_path / recipe["url_slug"]
        recipe_print_dir = recipe_dir / "p"
        recipe_qr_path = recipe_dir / "recipe-qr.png"

        make_recipe_page(recipe, recipe_dir, local)
        make_print_page(recipe, recipe_print_dir, local)
        qr.create(recipe["url"], recipe_qr_path)

        if recipe["has_image"]:
            shutil.copyfile(recipe["image_path"], recipe_dir / recipe["image"])
        if verbose:
            print(f'Recipe: {recipe["title"]}')

    for collection in site["collections"]:
        collection_dir = get_collection_dir(collection, site_path)
        make_collection_page(collection, collection_dir, local)
        if verbose:
            print(f'Collection: {collection["name"]}')

    make_404_page(site_path / "404.html")
    make_summary_page(site, timestamp, local, site_path / "summary.html")

    shutil.copyfile(
        os.path.join(utils.assets_directory, "icon.png"),
        os.path.join(site_path, "icon.png"),
    )
    shutil.copyfile(
        os.path.join(utils.assets_directory, "default_720x540.jpg"),
        os.path.join(site_path, "default.jpg"),
    )


def get_collection_dir(collection: dict, site_path: Path) -> Path:
    """Returns site directory for a collection page."""

    if collection["is_homepage"]:
        return site_path
    return site_path / collection["url_path"]


def make_recipe_page(recipe: dict, output_dir: Path, local: bool) -> None:
    """Create index.html file for recipe page.

    Args:
        recipe: Recipe data as a dictionary.
        output_dir: Path to build the page inside.
        local: Builds local version if true, web version otherwise.
    """

    utils.create_dir(output_dir)
    file_path = output_dir / "index.html"
    content = template.render(
        "recipe-page.html",
        r=recipe,
        icon=template.icons,
        site_title=utils.site_title(),
        is_local=local,
    )
    utils.write_file(content, file_path)


def make_print_page(recipe: dict, output_dir: Path, local: bool) -> None:
    """Create index.html file for recipe print page.

    Args:
        recipe: Recipe data as a dictionary.
        output_dir: Path to build the page inside.
        local: Builds local version if true, web version otherwise.
    """

    utils.create_dir(output_dir)
    file_path = output_dir / "index.html"
    content = template.render(
        "print-page.html",
        r=recipe,
        is_local=local,
        site_title=utils.site_title(),
        icon=template.icons,
    )
    utils.write_file(content, file_path)


def make_collection_page(collection: dict, collection_dir: Path, local: bool) -> None:
    """Create index.html file for collection page.

    Args:
        collection: Collection data as a dictionary.
        collection_dir: Path to build the page inside.
        local: Builds local version if true, web version otherwise.
    """

    utils.create_dir(collection_dir)
    file_path = collection_dir / "index.html"
    content = template.render(
        "collection.html",
        c=collection,
        is_local=local,
        site_title=utils.site_title(),
        icon=template.icons,
    )
    utils.write_file(content, file_path)


def make_summary_page(
    site: dict, timestamp: datetime.datetime, local: bool, page_path: Path
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


def make_404_page(page_path: Path) -> None:
    """Create 404 page for recipe site.

    Args:
        page_path: File path for 404 page.
    """

    content = template.render("404.html", site_title=utils.site_title())
    utils.write_file(content, page_path)
