"""
Configuring swaystatus to do your bidding.

Configuration is defined in a toml file located in one of the following places
(in order of preference):

    1. `--config-file=<FILE>`
    2. `$SWAYSTATUS_CONFIG_FILE`
    3. `<DIRECTORY>/config.toml` where `<DIRECTORY>` is from `--config-dir=<DIRECTORY>`
    4. `$SWAYSTATUS_CONFIG_DIR/config.toml`
    5. `$XDG_CONFIG_HOME/swaystatus/config.toml`
    6. `$HOME/.config/swaystatus/config.toml`

At the very minimum, the configuration file should contain the `order` key
which describes the desired elements and the order in which they will appear:

    order = ['hostname', 'clock']

Each name in the list corresponds to a python module file contained in a
package visible to swaystatus. The package could be in any of the following:

    1. A python package path given by `--include` (can be used multiple times).

    2. A python package called `modules` in the configuration directory. The
       first package that exists in the following list (in order of preference)
       will be visible:

          a. `<DIRECTORY>/modules/` where `<DIRECTORY>` is from `--config-dir=<DIRECTORY>`
          b. `$SWAYSTATUS_CONFIG_DIR/modules/`
          c. `$XDG_CONFIG_HOME/swaystatus/modules/`
          d. `$HOME/.config/swaystatus/modules/`

    3. A python package path specified in the configuration file:

        include = ['/path/to/package1', '/path/to/package2']

    4. A python package path specified in an environment variable:

        SWAYSTATUS_PACKAGE_PATH=/path/to/package1:/path/to/package2

    5. An installed python package with an entry point for `swaystatus.modules`
       defined like the following in the `pyproject.toml` (the package name
       could be anything).

          [project.entry-points."swaystatus.modules"]
          package = "awesome_swaystatus_modules"

Any combination of the above methods can be used. When looking for a particular
module, packages are searched in the order of preference defined above. If any
packages contain modules with the same name, the first package in the order
above that provides it will be used.

The following keys are recognized in the configuration file:

    `order`
        A list of the desired modules to display and their order. Each item can
        be of the form "name" or "name:instance". The latter form allows the
        same module to be used multiple times with different settings.

    `interval`
        A float specifying how often to update the status bar (in seconds,
        default: 1.0).

    `click_events`
        A boolean indicating whether or not to listen for status bar clicks
        (default: false).

    `include`
        A list of additional directories to treat as module packages (type:
        `list[str]`).

    `env`
        A dictionary of additional environment variables visible to click
        handlers (type: `dict[str, str]`).

    `on_click`
        A dictionary mapping pointer device button numbers to shell commands
        (type: `dict[int, str | list[str]]`).

    `settings`
        A dictionary mapping modules to keyword arguments that will be passed
        to the element constructor. The dictionary keys correspond to `order`
        key items mentioned earlier (type: `dict[str, dict[str, Any]]`.

A typical configuration file might look like the following:

    order = [
        'hostname',
        'path_exists:/mnt/foo',
        'memory',
        'clock',
        'clock:home'
    ]

    click_events = true

    [env]
    terminal = 'foot'

    [settings.hostname]
    full_text = "host: {}"

    [settings.path_exists]
    on_click.1 = '$terminal --working-directory="$instance"'
    on_click.2 = '$terminal --hold df "$instance"'

    [settings.clock.env]
    TZ = 'America/Chicago'

    [settings."clock:home".env]
    TZ = 'Asia/Tokyo'
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

from .element import BaseElement
from .logging import logger
from .modules import Modules


@dataclass(slots=True, kw_only=True, eq=False)
class Config:
    order: list[str] = field(default_factory=list)
    interval: float = 1.0
    click_events: bool = False
    settings: dict[str, Any] = field(default_factory=dict)
    include: list[str | Path] = field(default_factory=list)
    on_click: dict[int, str | list[str]] = field(default_factory=dict)
    env: dict[str, str] = field(default_factory=dict)

    @property
    def elements(self) -> Iterator[BaseElement]:
        """Yield all desired element constructors in the configured order."""
        modules = Modules(self.include)
        for key in self.order:
            try:
                name, instance = key.split(":", maxsplit=1)
            except ValueError:
                name, instance = key, None
            module = modules.load(name)
            if hasattr(module, "Element") and issubclass(module.Element, BaseElement):
                logger.info(f"Loaded {name} element from {module.__file__}")
                module.Element.name = name
                settings = deep_merge_dicts(
                    self.settings.get(name, {}),
                    self.settings.get(key, {}),
                )
                settings["env"] = self.env | settings.get("env", {})
                logger.debug(f"Initializing {name} element: {settings!r}")
                element = module.Element(**settings)
                element.instance = instance
                yield element


def deep_merge_dicts(first: dict, second: dict) -> dict:
    """Recursively merge the second dictionary into the first."""
    result = first.copy()
    for key, value in second.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    return result
