import sys
from functools import cached_property
from importlib import import_module, metadata
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import Iterable
from uuid import uuid4


class Modules:
    """Provide a way to locate and import swaystatus elements."""

    def __init__(self, include: Iterable[str | Path]) -> None:
        self.include = list(map(Path, include))
        self._cache: dict[str, ModuleType] = {}

    @cached_property
    def packages(self) -> list[str]:
        """Returns recognized module packages in order of preference."""
        result = []
        for package_dir in self.include:
            if (init_file := Path(package_dir).expanduser() / "__init__.py").is_file():
                package_name = str(uuid4()).replace("-", "")
                if spec := spec_from_file_location(package_name, init_file):
                    package = module_from_spec(spec)
                    sys.modules[package_name] = package
                    if spec.loader:
                        spec.loader.exec_module(package)
                        result.append(package_name)
        for entry_point in metadata.entry_points(group="swaystatus.modules"):
            result.append(entry_point.load().__name__)
        return result

    def load(self, name: str) -> ModuleType:
        """Return the first matching module."""
        if name not in self._cache:
            for package in self.packages:
                try:
                    self._cache[name] = import_module(f"{package}.{name}")
                    break
                except ModuleNotFoundError:
                    pass
            else:
                raise ModuleNotFoundError(f"Module not found in any package: {name}")
        return self._cache[name]
