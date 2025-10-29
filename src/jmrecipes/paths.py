from pathlib import Path

PROJECT_MARKERS = ("pyproject.toml", ".git")


def find_project_root(start: Path | None = None) -> Path:
    """Walk up from start (or CWD) until we find a directory with a project marker."""
    cur = (start or Path.cwd()).resolve()
    for parent in [cur, *cur.parents]:
        if any((parent / m).exists() for m in PROJECT_MARKERS):
            return parent
    return cur  # fallback if no marker found


class PathConfig:
    """Central place to resolve directories."""

    def __init__(self, project_dir: Path | None = None) -> None:
        self.project_dir = project_dir or find_project_root()
        self.builds_dir = self.project_dir / "builds"
        self.data_dir = self.project_dir / "data"
        self.assets_dir = self.data_dir / "assets"

    def ensure(self) -> "PathConfig":
        """Make sure the dirs exist."""
        self.builds_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        return self
