import shutil
import sys
from pathlib import Path
from typing import Callable

from pytest import fixture, raises
from pytest_mock import MockerFixture

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


type TemporaryPackageFactory = Callable[[], TemporaryPackage]


@fixture
def tmp_package_factory(tmp_path) -> TemporaryPackageFactory:
    names: list[str] = []

    def factory() -> TemporaryPackage:
        name = f"package{len(names)}"
        names.append(name)
        return TemporaryPackage(tmp_path / "packages" / name)

    return factory


class TestRegistry:
    def test_module_empty_registry(self) -> None:
        """Requesting a module from an empty registry will raise an error."""
        package_registry = PackageRegistry([])
        with raises(ModuleNotFoundError):
            package_registry.module("foo")

    def test_module_missing(self, tmp_package_factory: TemporaryPackageFactory) -> None:
        """Requesting a non-existent module from a non-empty registry will raise an error."""
        package = tmp_package_factory()
        package_registry = PackageRegistry([package.directory])
        with raises(ModuleNotFoundError):
            package_registry.module("foo")

    def test_module_found(self, tmp_package_factory: TemporaryPackageFactory) -> None:
        """An existing module will be found in a valid package."""
        package = tmp_package_factory()
        module_path = package.add_module("foo")
        package_registry = PackageRegistry([package.directory])
        Element = package_registry.module("foo")
        assert sys.modules[Element.__module__].__file__ == str(module_path)

    def test_module_earliest_preferred(self, tmp_package_factory: TemporaryPackageFactory) -> None:
        """A module package included earlier is preferred when looking for a module."""
        package1 = tmp_package_factory()
        package2 = tmp_package_factory()
        module_path1 = package1.add_module("foo")
        package2.add_module("foo")
        package_registry = PackageRegistry([package1.directory, package2.directory])
        Element = package_registry.module("foo")
        assert sys.modules[Element.__module__].__file__ == str(module_path1)

    def test_entry_points(self, mocker: MockerFixture, tmp_package_factory: TemporaryPackageFactory) -> None:
        """A module package defined as an entry point is recognized."""

        class Package:
            __name__ = "test"

        class EntryPoint:
            def load(self):
                return Package()

        package = tmp_package_factory()
        mock = mocker.patch("importlib.metadata.entry_points", return_value=[EntryPoint()])
        package_registry = PackageRegistry([package.directory])
        assert len(package_registry.packages) == 2
        mock.assert_called_once_with(group="swaystatus.modules")
        assert package_registry.packages[-1] == "test"
