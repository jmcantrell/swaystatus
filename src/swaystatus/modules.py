"""
Locate and load content generation elements stored in modules.

A status bar element (a subclass of `swaystatus.BaseElement`) must be named
`Element` and must be stored in a module file at the top level of a package
that is visible in any or all of the following places (in order of preference):

    1. `--include=<DIRECTORY>` (can be used multiple times)

    2. A python package in the data directory (in order of preference):

          a. `--data-dir=<DIRECTORY>`
          b. `$SWAYSTATUS_DATA_DIR/modules`
          c. `$XDG_DATA_HOME/swaystatus/modules`

    3. Included in the configuration file:

        include = ['/path/to/package1', '/path/to/package2']

    4. A python package path specified in an environment variable:

        SWAYSTATUS_PACKAGE_PATH="/path/to/package1:/path/to/package2"

    5. A python package with an entry point for `swaystatus.modules` defined
       like the following in the `pyproject.toml`:

          [project.entry-points."swaystatus.modules"]
          package = "awesome_swaystatus_modules"

When a module is found and imported, the the `Element.name` class attribute is
assigned the name used to look it up. This is done so that the class can be
located when delegating click events.

See the documentation for `swaystatus.element` to learn about creating elements.
"""

import sys
from functools import cache, cached_property
from importlib import import_module, metadata
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import Iterable
from uuid import uuid4

from .element import BaseElement
from .logging import logger


class Modules:
    """Provide a way to locate and import swaystatus elements."""

    def __init__(self, include: Iterable[str | Path] | None = None) -> None:
        self.include = list(map(Path, include or []))

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

    @cache
    def load(self, name: str) -> ModuleType:
        """Return the first matching module in any visible packages."""
        for package in self.packages:
            try:
                module = import_module(f"{package}.{name}")
                if hasattr(module, "Element") and issubclass(module.Element, BaseElement):
                    logger.debug(f"Imported module: {module!r}")
                    module.Element.name = name
                    return module
            except ModuleNotFoundError:
                pass
        else:
            raise ModuleNotFoundError(f"Module not found in any package: {name}")


__all__ = [Modules.__name__]
