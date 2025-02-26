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

The following keys are recognized in the configuration file:

    `order` (type: `list[str]`)
        The desired modules to display and their order. Each item can be of the
        form "name" or "name:instance". The latter form allows the same module
        to be used multiple times with different settings.

    `interval` (type: `float`, default: `5.0`)
        How often (in seconds) to update the status bar.

    `click_events` (type: `bool`, default: `false`)
        Whether or not to listen for status bar clicks.

    `include` (type: `list[str]`, default: `[]`)
        Additional directories to treat as module packages.

    `env` (type: `dict[str, str]`, default: `{}`)
        Additional environment variables visible to click handlers.

    `on_click` (type: `dict[int, str | list[str]]`, default: `{}`)
        Maps pointer button numbers to shell commands that should be run in
        response to a click by that button.

    `settings` (type: `dict[str, dict[str, Any]]`)
        Maps module specifiers (as defined in `order`) to keyword arguments
        that will be passed to the element constructor.

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
    on_click.1 = '$terminal --hold hostnamectl'

    [settings.path_exists]
    on_click.1 = ['$terminal', '--working-directory=$instance']
    on_click.2 = ['$terminal', '--hold', 'df', '$instance']

    [settings.clock]
    on_click.1 = '$terminal --hold cal'

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

default_interval = 5.0


@dataclass(slots=True, kw_only=True, eq=False)
class Config:
    order: list[str] = field(default_factory=list)
    interval: float = default_interval
    click_events: bool = False
    settings: dict[str, Any] = field(default_factory=dict)
    include: list[str | Path] = field(default_factory=list)
    on_click: dict[int, str | list[str]] = field(default_factory=dict)
    env: dict[str, str] = field(default_factory=dict)

    @property
    def elements(self) -> Iterator[BaseElement]:
        """Yield all desired element constructors in the configured order."""
        modules = Modules(self.include)
        for i, key in enumerate(self.order):
            try:
                name, instance = key.split(":", maxsplit=1)
            except ValueError:
                name, instance = key, None
            assert name, f"Missing module name for item {i} in `order`: {key}"
            module = modules.load(name)
            logger.info(f"Loaded {name} element from {module.__file__}")
            settings = deep_merge_dicts(
                self.settings.get(name, {}),
                self.settings.get(key, {}),
            )
            settings["env"] = self.env | settings.get("env", {})
            if instance:
                settings["env"]["instance"] = instance
            logger.debug(f"Initializing {key} element: {settings!r}")
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
