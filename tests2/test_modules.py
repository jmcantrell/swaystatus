import shutil
import sys
from contextlib import contextmanager
from importlib.metadata import EntryPoint
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterator
from unittest import TestCase, main
from unittest.mock import MagicMock, patch

from swaystatus.modules import PackageRegistry


class TemporaryPackage:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        (self.directory / "__init__.py").touch()

    def __str__(self) -> str:
        return str(self.directory)

    def add_module(self, name: str) -> Path:
        src_path = Path(__file__).parent / "data/module.py"
        dst_path = self.directory / f"{name}.py"
        shutil.copyfile(src_path, dst_path)
        return dst_path


@contextmanager
def temp_package() -> Iterator[TemporaryPackage]:
    with TemporaryDirectory() as temp_dir:
        yield TemporaryPackage(Path(temp_dir))


class TestPackageRegistry(TestCase):
    def test_module_empty(self) -> None:
        package_registry = PackageRegistry([])
        with self.assertRaises(ModuleNotFoundError):
            package_registry.module("foo")

    def test_module_missing(self) -> None:
        with temp_package() as package:
            package_registry = PackageRegistry([package.directory])
            with self.assertRaises(ModuleNotFoundError):
                package_registry.module("foo")

    def test_module_found(self) -> None:
        with temp_package() as package:
            module_path = package.add_module("foo")
            package_registry = PackageRegistry([package.directory])
            Element = package_registry.module("foo")
            self.assertEqual(sys.modules[Element.__module__].__file__, str(module_path))

    def test_module_prefer_early(self) -> None:
        with temp_package() as package1, temp_package() as package2:
            module_path1 = package1.add_module("foo")
            package2.add_module("foo")
            package_registry = PackageRegistry([package1.directory, package2.directory])
            Element = package_registry.module("foo")
            self.assertEqual(sys.modules[Element.__module__].__file__, str(module_path1))

    def test_entry_points(self) -> None:

        class Package:
            __name__ = "test"

        entry_point_mock = MagicMock(spec=EntryPoint)
        entry_point_mock.load.return_value = Package()

        with patch("importlib.metadata.entry_points", return_value=[entry_point_mock]) as group_mock:
            with temp_package() as package:
                package_registry = PackageRegistry([package.directory])
                self.assertEqual(len(package_registry.packages), 2)
                group_mock.assert_called_once_with(group="swaystatus.modules")
                self.assertEqual(package_registry.packages[-1], "test")
                entry_point_mock.load.assert_called_once()


if __name__ == "__main__":
    main()
