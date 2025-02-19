import sys
from functools import cached_property
from importlib import import_module, metadata
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import Iterable
from uuid import uuid4


def unique_package_name() -> str:
    return str(uuid4()).replace("-", "")


class Modules:
    def __init__(self, include: Iterable[Path]):
        self.include = list(include)
        self.cache: dict[str, ModuleType] = {}

    @cached_property
    def packages(self) -> list[str]:
        result = []

        for i, modules_dir in enumerate(self.include):
            if (init_file := modules_dir.expanduser() / "__init__.py").is_file():
                package_name = unique_package_name()
                if spec := spec_from_file_location(package_name, init_file):
                    package = module_from_spec(spec)
                    sys.modules[package_name] = package
                    if spec.loader:
                        spec.loader.exec_module(package)
                        result.append(package_name)

        for entry_point in metadata.entry_points(group="swaystatus.modules"):
            result.append(entry_point.load().__name__)

        return result

    def find(self, name: str) -> ModuleType:
        if name not in self.cache:
            for package in self.packages:
                try:
                    self.cache[name] = import_module(f"{package}.{name}")
                    break
                except ModuleNotFoundError:
                    continue
            else:
                raise ModuleNotFoundError(f"Module not found in any package: {name}")

        return self.cache[name]
