from pathlib import Path
from unittest import TestCase, main

from swaystatus.paths import path_normalized


class PathLike:
    def __init__(self, path: str) -> None:
        self.path = path

    def __fspath__(self) -> str:
        return self.path


class TestPathNormalized(TestCase):
    def test_absolute(self) -> None:
        self.assertEqual(path_normalized("/path"), Path("/path"))
        self.assertEqual(path_normalized(PathLike("/path")), Path("/path"))

    def test_relative(self) -> None:
        self.assertEqual(path_normalized("path"), Path.cwd() / "path")
        self.assertEqual(path_normalized(PathLike("path")), Path.cwd() / "path")

    def test_user(self) -> None:
        self.assertEqual(path_normalized("~/path"), Path.home() / "path")
        self.assertEqual(path_normalized(PathLike("~/path")), Path.home() / "path")

    def test_resolve(self) -> None:
        self.assertEqual(path_normalized("/dir/../path"), Path("/path"))
        self.assertEqual(path_normalized(PathLike("/dir/../path")), Path("/path"))


if __name__ == "__main__":
    main()
