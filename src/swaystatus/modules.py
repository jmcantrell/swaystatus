import sys
from uuid import uuid4
from pathlib import Path
from importlib import import_module, metadata
from importlib.util import spec_from_file_location, module_from_spec


class Modules:
    def __init__(self, include):
        self._packages = []
        self._cached_modules = {}

        for i, modules_dir in enumerate(include):
            if (init_file := Path(modules_dir).expanduser() / "__init__.py").is_file():
                package_name = str(uuid4()).replace("-", "")
                if spec := spec_from_file_location(package_name, init_file):
                    package = module_from_spec(spec)
                    sys.modules[package_name] = package
                    if spec.loader:
                        spec.loader.exec_module(package)
                        self._packages.append(package_name)

        for entry_point in metadata.entry_points(group="swaystatus.modules"):
            self._packages.append(entry_point.load().__name__)

    def find(self, name):
        if name not in self._cached_modules:
            for package in self._packages:
                try:
                    self._cached_modules[name] = import_module(f"{package}.{name}")
                    break
                except ModuleNotFoundError:
                    continue
            else:
                raise ModuleNotFoundError(f"Module not found in any package: {name}")

        return self._cached_modules[name]
