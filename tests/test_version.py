import tomllib
from pathlib import Path

import swaystatus


def test_version_matches() -> None:
    """The package version matches the project version."""
    metadata_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with metadata_path.open("rb") as file:
        project_version = tomllib.load(file)["project"]["version"]
    assert swaystatus.__version__ == project_version
