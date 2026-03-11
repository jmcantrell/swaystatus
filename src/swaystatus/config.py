"""
Runtime configuration for swaystatus.

Configuration is defined in one of the following files (in order of
preference):

    1. --config-file=<FILE>

    2. $SWAYSTATUS_CONFIG_FILE

    3. <DIRECTORY>/config.toml where <DIRECTORY> is from --config-dir=<DIRECTORY>

    4. $SWAYSTATUS_CONFIG_DIR/config.toml

    5. $XDG_CONFIG_HOME/swaystatus/config.toml

    6. $HOME/.config/swaystatus/config.toml

The following keys are recognized at the top-level of the file:

    `interval` (type: float | int | None, default: None)
        How often (in seconds) to update the status bar.

    `click_events` (type: bool, default: False)
        Whether to listen for clicks on status bar blocks.

    `include` (type: list[str], default: [])
        Additional directories to treat as module packages.

    `env` (type: dict[str, str], default: {})
        Environment changes for every module.

    `settings` (type: dict[str, dict], default: {})
        Configuration inherited by all modules of the same name.

    `modules` (type: list[dict], default: [])
        The modules to be displayed in the status line.

Each `settings[name]` entry recognizes the following keys:

    `env` (type: dict[str, str], default: {})
        Environment changes for this module group.

    `on_click` (type: dict[int, str | list[str]], default: {})
        Click handlers for this module group.

    `params` (type: dict[str, Any], default: {})
        Instance parameters for this module group.

Each item in the `modules` list recognizes the following keys:

    `name` (type: str, required)
        Specify the module to be loaded.

    `instance` (type: str | None, default: None)
        Differentiate this module from others of the same `name`.

    `env` (type: dict[str, str], default: {})
        Environment changes for this module. Merged with those in `settings`.

    `on_click` (type: dict[int, str | list[str]], default: {})
        Click handlers for this module. Merged with those in `settings`.

    `params` (type: dict[str, Any], default: {})
        Instance parameters for this module. Merged with those in `settings`.
"""

import tomllib
from dataclasses import dataclass, field
from functools import cache, cached_property
from typing import Any, Iterator, Mapping, NotRequired, Self, Sequence, TypedDict

from .typing import PathLike, Seconds

type EnvDict = dict[str, str | None]
type ModuleKey = tuple[str, str | None]
type OnClickDict = dict[int, str | Sequence[str]]
type ParamsDict = dict[str, Any]


class SettingsDict(TypedDict):
    env: NotRequired[EnvDict]
    on_click: NotRequired[OnClickDict]
    params: NotRequired[ParamsDict]


class ModuleDict(SettingsDict):
    name: str
    instance: NotRequired[str | None]


@dataclass(kw_only=True, eq=False)
class Config:
    """Data class representing runtime configuration."""

    interval: Seconds = None
    click_events: bool = False
    env: EnvDict = field(default_factory=dict)
    include: list[PathLike] = field(default_factory=list)
    settings: dict[str, SettingsDict] = field(default_factory=dict)
    modules: list[ModuleDict] = field(default_factory=list)

    @cached_property
    def _modules_lookup(self) -> Mapping[ModuleKey, ModuleDict]:
        return {(m["name"], m.get("instance")): m for m in self.modules}

    def module_keys(self) -> Iterator[ModuleKey]:
        """Yield the configured module identifiers in order."""
        for module in self.modules:
            yield module["name"], module.get("instance")

    @cache
    def module(self, name: str, instance: str | None = None) -> ParamsDict:
        """Return a module's merged keyword arguments suitable for an element class instantiation."""
        module = self._modules_lookup[(name, instance)]
        kwargs: ParamsDict = {}
        settings = self.settings.get(name, {})
        if params := settings.get("params"):
            kwargs.update(params)
        if params := module.get("params"):
            kwargs.update(params)
        if self.env:
            kwargs.setdefault("env", {}).update(self.env)
        if env := settings.get("env"):
            kwargs.setdefault("env", {}).update(env)
        if env := module.get("env"):
            kwargs.setdefault("env", {}).update(env)
        if on_click := settings.get("on_click"):
            kwargs.setdefault("on_click", {}).update(on_click)
        if on_click := module.get("on_click"):
            kwargs.setdefault("on_click", {}).update(on_click)
        for key in ["name", "instance"]:
            try:
                del kwargs[key]
            except KeyError:
                pass
        return kwargs

    @classmethod
    def from_file(cls, path: PathLike) -> Self:
        """Instantiate a configuration object from a toml file."""
        with open(path, "rb") as file:
            data = tomllib.load(file)
        if settings := data.get("settings"):
            for name, module_settings in settings.items():
                if on_click := module_settings.get("on_click"):
                    module_settings["on_click"] = {int(b): c for b, c in on_click.items()}
        if modules := data.get("modules"):
            for module in modules:
                if on_click := module.get("on_click"):
                    module["on_click"] = {int(b): c for b, c in on_click.items()}
        return cls(**data)
