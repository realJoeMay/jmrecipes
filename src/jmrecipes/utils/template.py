"""Template rendering utilities and SVG icon definitions."""

import os
import jinja2

from jmrecipes.paths import get_paths


def render(template_name: str, **context) -> str:
    """Render a Jinja2 template with the provided context."""
    templates_dir = get_paths().templates_dir

    try:
        _environment = jinja2.Environment(loader=jinja2.FileSystemLoader(templates_dir))
        template = _environment.get_template(template_name)
    except jinja2.TemplateNotFound as exc:
        raise ValueError(
            f"Template '{template_name}' not found in '{templates_dir}'."
        ) from exc
    return template.render(context)


def get_icons() -> dict:
    """Return SVG icons from subfolder.

    Returns:
        dict: A dictionary mapping filename stem (without extension) to SVG contents.
              Example: {'gear': '<svg>...</svg>', 'home': '<svg>...</svg>'}
    """
    icons_dir = get_paths().icons_dir

    icons = {}

    for filename in os.listdir(icons_dir):
        if filename.endswith(".svg"):
            filepath = os.path.join(icons_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    name = os.path.splitext(filename)[0]  # remove .svg extension
                    icons[name] = f.read()
            except OSError as e:
                print(f"Error loading icon {filename}: {e}")
    return icons
