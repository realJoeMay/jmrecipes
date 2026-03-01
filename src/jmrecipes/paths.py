"""Path handling for jmrecipes."""

from pathlib import Path
from typing import Optional

_paths: Optional["PathConfig"] = None

PROJECT_MARKERS = ("pyproject.toml", ".git")


def find_project_root(start: Path | None = None) -> Path:
    """Walk up from start (or CWD) until we find a directory with a project marker."""
    cur = (start or Path.cwd()).resolve()
    for parent in [cur, *cur.parents]:
        if any((parent / m).exists() for m in PROJECT_MARKERS):
            return parent
    return cur  # fallback if no marker found


class PathConfig:
    """Centralized resolver for project directories and files."""

    def __init__(self, project_dir: Path, data_dir: Path):
        """Initialize path configuration with project and data roots."""
        self._project_dir = project_dir
        self._data_dir = data_dir

    @property
    def project_dir(self) -> Path:
        """Return the root directory of the project."""
        return self._project_dir

    @property
    def builds_dir(self) -> Path:
        """Return the directory where generated builds are written."""
        return self.project_dir / "builds"

    @property
    def templates_dir(self) -> Path:
        """Return the directory containing HTML templates."""
        return self.project_dir / "src" / "jmrecipes" / "templates"

    @property
    def icons_dir(self) -> Path:
        """Return the directory containing SVG icon assets."""
        return self.project_dir / "src" / "jmrecipes" / "utils" / "icons"

    @property
    def data_dir(self) -> Path:
        """Return the directory containing input data files."""
        return self._data_dir

    @property
    def config_file(self) -> Path:
        """Return the path to the main configuration file."""
        return self.data_dir / "config.ini"

    @property
    def assets_dir(self) -> Path:
        """Return the directory containing static data assets."""
        return self.data_dir / "assets"


def init_paths(
    project_dir: Path | None = None, data_dir: Path | str | None = None
) -> None:
    """Initialize global path configuration."""
    global _paths  # pylint: disable=global-statement
    if _paths is not None:
        raise RuntimeError("Paths already initialized")

    project_dir = (project_dir or find_project_root()).resolve()
    _paths = PathConfig(
        project_dir=project_dir,
        data_dir=(Path(data_dir) if data_dir else project_dir / "data").resolve(),
    )


def get_paths() -> PathConfig:
    """Return path configuration."""
    if _paths is None:
        init_paths()  # auto-initialize with defaults if not already done

    if _paths is None:
        raise RuntimeError("Paths not initialized")

    return _paths
