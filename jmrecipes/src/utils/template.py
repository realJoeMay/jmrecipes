"""Template rendering utilities and SVG icon definitions."""

import os
import jinja2


# Directories
utils_directory = os.path.dirname(os.path.abspath(__file__))
src_directory = os.path.split(utils_directory)[0]
templates_directory = os.path.join(src_directory, "templates")
icons_directory = os.path.join(utils_directory, "icons")

_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(templates_directory))


def render(template_name: str, **context) -> str:
    """Render a Jinja2 template with the provided context."""

    try:
        template = _environment.get_template(template_name)
    except jinja2.TemplateNotFound as exc:
        raise ValueError(
            f"Template '{template_name}' not found in '{templates_directory}'."
        ) from exc
    return template.render(context)


def _load_icons() -> dict:
    """Return SVG icons from subfolder.

    Returns:
        dict: A dictionary mapping filename stem (without extension) to SVG contents.
              Example: {'gear': '<svg>...</svg>', 'home': '<svg>...</svg>'}
    """

    loaded_icons = {}

    for filename in os.listdir(icons_directory):
        if filename.endswith(".svg"):
            filepath = os.path.join(icons_directory, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    name = os.path.splitext(filename)[0]  # remove .svg extension
                    loaded_icons[name] = f.read()
            except OSError as e:
                print(f"Error loading icon {filename}: {e}")
    return loaded_icons


icons = _load_icons()
