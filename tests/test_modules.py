import shutil
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from importlib.metadata import EntryPoint
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from unittest.mock import MagicMock, patch

from swaystatus.modules import ModuleNotFound, Registry


class TestRegistry(TestCase):
    def test_repr(self) -> None:
        modules = Registry([])
        modules.packages = ["package1", "package2", "package3"]
        self.assertEqual(repr(modules), repr(modules.packages))

    def test_find_empty(self) -> None:
        modules = Registry([])
        with self.assertRaises(ModuleNotFound):
            modules.find("foo")

    def test_find_missing(self) -> None:
        with temp_package() as package:
            modules = Registry([package.directory])
            with self.assertRaises(ModuleNotFound):
                modules.find("foo")

    def test_find_found(self) -> None:
        with temp_package() as package:
            module_path = package.add_module("foo")
            modules = Registry([package.directory])
            Element = modules.find("foo")
            self.assertEqual(sys.modules[Element.__module__].__file__, str(module_path))

    def test_find_prefer_early(self) -> None:
        with temp_package() as package1, temp_package() as package2:
            module_path1 = package1.add_module("foo")
            package2.add_module("foo")
            modules = Registry([package1.directory, package2.directory])
            Element = modules.find("foo")
            self.assertEqual(sys.modules[Element.__module__].__file__, str(module_path1))

    def test_entry_points(self) -> None:
        class Package:
            __name__ = "test"

        entry_point_mock = MagicMock(spec=EntryPoint)
        entry_point_mock.load.return_value = Package()

        with (
            temp_package() as package,
            patch("importlib.metadata.entry_points", return_value=[entry_point_mock]) as group_mock,
        ):
            modules = Registry([package.directory])
            self.assertEqual(len(modules.packages), 2)
            group_mock.assert_called_once_with(group="swaystatus.modules")
            self.assertEqual(modules.packages[-1], "test")
            entry_point_mock.load.assert_called_once()


class TemporaryPackage:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        (self.directory / "__init__.py").touch()

    def __str__(self) -> str:
        return str(self.directory)

    def add_module(self, name: str) -> Path:
        src_path = Path(__file__).parent / "data/modules/test.py"
        dst_path = self.directory / f"{name}.py"
        shutil.copyfile(src_path, dst_path)
        return dst_path


@contextmanager
def temp_package() -> Iterator[TemporaryPackage]:
    with TemporaryDirectory() as temp_dir:
        yield TemporaryPackage(Path(temp_dir))


if __name__ == "__main__":
    main()
