"""
Runtime configuration for swaystatus.

Configuration is defined in a toml file located in one of the following places
(in order of preference):

    1. `--config-file=<FILE>`
    2. `$SWAYSTATUS_CONFIG_FILE`
    3. `<DIRECTORY>/config.toml` where `<DIRECTORY>` is from `--config-dir=<DIRECTORY>`
    4. `$SWAYSTATUS_CONFIG_DIR/config.toml`
    5. `$XDG_CONFIG_HOME/swaystatus/config.toml`
    6. `$HOME/.config/swaystatus/config.toml`

The following keys are recognized in the configuration file:

    `order` (type: `list[str]`, default: `[]`)
        The desired elements to display and their order. Each item can be of
        the form "name" or "name:instance". The latter form allows the same
        element to be used multiple times with different settings for each
        "instance".

    `interval` (type: `float|None`, default: `None`)
        How often (in seconds) to update the status bar. If set to `None`, the
        status bar will only update on initialization or when signaled.

    `click_events` (type: `bool`, default: `false`)
        Whether or not to listen for status bar clicks.

    `include` (type: `list[str]`, default: `[]`)
        Additional directories to treat as element packages.

    `env` (type: `dict[str, str]`, default: `{}`)
        Additional environment variables visible to click handlers.

    `on_click` (type: `dict[int, str | list[str]]`, default: `{}`)
        Maps pointer button numbers to shell commands that should be run in
        response to a click by that button.

    `settings` (type: `dict[str, dict[str, Any]]`, default: `{}`)
        Maps element specifiers (as defined in `order`) to keyword arguments
        that will be passed to the element constructor.

A typical configuration file might look like the following:

    order = [
        'hostname',
        'path_exists:/mnt/foo',
        'memory',
        'clock',
        'clock:home'
    ]

    interval = 5.0
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

    [settings."clock:home".env]
    TZ = 'Asia/Tokyo'
"""

import tomllib
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Any, Iterator, Self

from .element import ShellCommand

type Settings = dict[str, Any]


@dataclass(kw_only=True, eq=False)
class Config:
    """Data class representing runtime configuration."""

    order: list[str] = field(default_factory=list)
    interval: float | None = None
    click_events: bool = False
    settings: dict[str, Any] = field(default_factory=dict)
    include: list[str | Path] = field(default_factory=list)
    on_click: dict[int, ShellCommand] = field(default_factory=dict)
    env: dict[str, str] = field(default_factory=dict)

    @cached_property
    def elements(self) -> Iterator[tuple[str, Settings]]:
        """Return the name and settings for each configured element in order."""
        for key in self.order:
            name, instance = decode_element_key(key)
            settings = self.settings.get(name, {})
            if instance:
                settings = deep_merge_dicts(settings, self.settings.get(key, {}))
            settings["env"] = self.env | settings.get("env", {})
            settings["instance"] = instance
            yield name, settings

    @classmethod
    def from_file(cls, path: Path) -> Self:
        """Instantiate a configuration object from a toml file."""
        with path.open("rb") as file:
            return cls(**tomllib.load(file))


def decode_element_key(key: str) -> tuple[str, str | None]:
    """Parse a name and instance from a string like "name" or "name:instance"."""
    name, sep, instance = key.partition(":")
    if not name:
        raise ValueError("Missing element name")
    if not sep:
        return name, None
    return name, instance or None


def deep_merge_dicts(first: dict, second: dict) -> dict:
    """Recursively merge the second dictionary into the first."""
    result = first.copy()
    for key, value in second.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


__all__ = [Config.__name__]
