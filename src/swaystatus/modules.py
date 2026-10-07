"""Locate and load status bar content generation elements stored in module packages."""

import sys
from collections.abc import Iterable
from functools import cached_property
from importlib import import_module, metadata
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from uuid import uuid4

from .element import BaseElement
from .logger import logger


class ModuleNotFound(Exception):
    """Exception to indicate that a requested module was not found."""

    def __init__(self, name: str) -> None:
        super().__init__(f"module not found in any package: {name}")
        self.name = name


class Registry:
    """Track, locate, and import status bar modules."""

    def __init__(self, directories: Iterable[Path]) -> None:
        """
        Initialize a module package registry.

        The directories passed will be treated as module packages if they look
        like python packages.
        """

        self.directories = directories

    def __repr__(self) -> str:
        return repr(self.packages)

    @cached_property
    def packages(self) -> list[str]:
        """
        Return module package names (in order of preference).

        A directory in the `directories` instance attribute will be treated as
        a module package if it looks like a python package. Additionally, any
        installed python packages with the entry point "swaystatus.modules"
        defined will be included.
        """

        package_names = []

        for package_dir in self.directories:
            if (init_file := package_dir / "__init__.py").is_file():
                package_name = str(uuid4()).replace("-", "")
                if spec := spec_from_file_location(package_name, init_file):
                    package = module_from_spec(spec)
                    sys.modules[package_name] = package
                    if spec.loader:
                        spec.loader.exec_module(package)
                        package_names.append(package_name)

        for entry_point in metadata.entry_points(group="swaystatus.modules"):
            package_names.append(entry_point.load().__name__)

        return package_names

    def find(self, module_name: str) -> type[BaseElement]:
        """
        Return the first matching element class in any visible module package.

        For an element class to be found, it must be named `Element`, subclass
        `swaystatus.BaseElement`, and be stored at the top level of a module
        package in a file named like `<module_name>.py`.
        """

        for package in self.packages:
            try:
                module = import_module(f"{package}.{module_name}")
                if hasattr(module, "Element") and issubclass(module.Element, BaseElement):
                    logger.debug("imported module %r", module)
                    module.Element.name = module_name
                    return module.Element
            except ModuleNotFoundError:
                pass

        raise ModuleNotFound(module_name)


__all__ = [
    Registry.__name__,
    ModuleNotFound.__name__,
]
