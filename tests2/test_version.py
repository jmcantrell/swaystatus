import tomllib
from pathlib import Path
from unittest import TestCase, main

import swaystatus


class TestVersion(TestCase):
    def test_matches_project(self) -> None:
        metadata_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
        with metadata_path.open("rb") as file:
            project_version = tomllib.load(file)["project"]["version"]
        self.assertEqual(swaystatus.__version__, project_version)


if __name__ == "__main__":
    main()
