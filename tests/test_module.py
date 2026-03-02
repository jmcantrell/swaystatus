import shutil
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from unittest.mock import patch

from swaystatus.module import ModuleRegistry


class TemporaryModulePackage:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        (self.directory / "__init__.py").touch()

    def __str__(self) -> str:
        return str(self.directory)

    def add_module(self, name: str, source="empty") -> Path:
        src_path = Path(__file__).parent / "modules" / f"{source}.py"
        dst_path = self.directory / f"{name}.py"
        shutil.copyfile(src_path, dst_path)
        return dst_path


class TestModuleRegistry(TestCase):
    def temp_package(self) -> TemporaryModulePackage:
        return TemporaryModulePackage(Path(self.enterContext(TemporaryDirectory(prefix="test_module"))))

    def test_get_exists(self) -> None:
        """Test that an existing module will be found in a valid package."""
        package = self.temp_package()
        module_name = "foo"
        module_path = package.add_module(module_name)
        modules = ModuleRegistry([package.directory])
        Element = modules.get(module_name)
        self.assertEqual(sys.modules[Element.__module__].__file__, str(module_path))

    def test_get_not_exists(self) -> None:
        """Test that requesting a non-existent module will raise an error."""
        with self.assertRaises(ModuleNotFoundError):
            registry = ModuleRegistry([])
            registry.packages = []
            registry.get("foo")

    def test_get_earliest_preferred(self) -> None:
        """Test that a module package included earlier is preferred when looking for a module."""
        package1 = self.temp_package()
        package2 = self.temp_package()
        name = "foo"
        module_path1 = package1.add_module(name)
        package2.add_module(name)
        registry = ModuleRegistry([package1.directory, package2.directory])
        Element = registry.get(name)
        self.assertEqual(sys.modules[Element.__module__].__file__, str(module_path1))

    def test_entry_points(self) -> None:
        """Test that a module package defined as an entry point is recognized."""

        package_name = "test"

        class Package:
            __name__ = package_name

        class EntryPoint:
            def load(self):
                return Package()

        package = self.temp_package()

        with patch("importlib.metadata.entry_points", return_value=[EntryPoint()]) as mock:
            registry = ModuleRegistry([package.directory])
            self.assertEqual(len(registry.packages), 2)
            mock.assert_called_once_with(group="swaystatus.modules")
            self.assertEqual(registry.packages[-1], package_name)


if __name__ == "__main__":
    main()
