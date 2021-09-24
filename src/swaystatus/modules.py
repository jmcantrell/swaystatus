import sys
from uuid import uuid4
from pathlib import Path
from importlib import import_module, metadata
from importlib.util import spec_from_file_location, module_from_spec


class Modules:
    def __init__(self, include):
        self._packages = []

        for i, modules_dir in enumerate(include):
            package_name = str(uuid4()).replace("-", "_")
            package_init_file = Path(modules_dir) / "__init__.py"
            if package_init_file.is_file():
                spec = spec_from_file_location(package_name, package_init_file)
                if spec:
                    package = module_from_spec(spec)
                    sys.modules[package_name] = package
                    spec.loader.exec_module(package)
                    self._packages.append(package_name)

        entry_points = metadata.entry_points().get("swaystatus.modules", [])

        for entry_point in entry_points:
            self._packages.append(entry_point.load().__name__)

    def find(self, module):
        for package in self._packages:
            try:
                return import_module(f"{package}.{module}")
            except ModuleNotFoundError:
                continue
        else:
            raise ModuleNotFoundError(
                f"No module named '{module}' in any modules package"
            )
