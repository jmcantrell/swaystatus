import tomllib
from pathlib import Path

from swaystatus.version import version


def test_version_matches_project() -> None:
    """Ensure that the package version matches the project version."""
    project_file = Path(__file__).resolve().parents[1] / "pyproject.toml"
    project_version = tomllib.load(project_file.open("rb"))["project"]["version"]
    assert version == project_version
