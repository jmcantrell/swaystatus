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
from functools import cached_property
from pathlib import Path
from typing import Any, Iterator, Mapping, NotRequired, Self, Sequence, TypedDict

type EnvDict = dict[str, str | None]
type ModuleKey = tuple[str, str | None]
type OnClickDict = dict[int, str | Sequence[str]]
type ParamsDict = dict[str, Any]

MISSING = object()


class SettingsDict(TypedDict):
    env: NotRequired[EnvDict]
    on_click: NotRequired[OnClickDict]
    params: NotRequired[ParamsDict]


class ModuleDict(SettingsDict):
    name: str
    instance: NotRequired[str]


@dataclass(kw_only=True)
class Config:
    """Data class representing runtime configuration."""

    interval: float | int | None = None
    click_events: bool = False
    env: EnvDict = field(default_factory=dict)
    include: list[str | Path] = field(default_factory=list)
    settings: dict[str, SettingsDict] = field(default_factory=dict)
    modules: list[ModuleDict] = field(default_factory=list)

    def __setattr__(self, name: str, value: object) -> None:
        if validator := getattr(self, f"_validate_{name}", None):
            value = validator(value)
        super().__setattr__(name, value)

    def _validate_interval(self, interval: object) -> float | int | None:
        if interval is None:
            return None
        if not isinstance(interval, float | int):
            raise TypeError(f"must be float or int, got {type(interval).__name__}")
        if interval <= 0:
            raise ValueError("must be positive")
        return interval

    def _validate_click_events(self, click_events: object) -> bool:
        if not isinstance(click_events, bool):
            raise TypeError(f"must be bool, got {type(click_events).__name__}")
        return click_events

    def _validate_env(self, env: object) -> EnvDict:
        return _ensure_env_dict(env)

    def _validate_include(self, include: object) -> list[Path]:
        if not isinstance(include, list):
            raise TypeError(f"must be list, got {type(include).__name__}")
        for i, path in enumerate(include):
            if not isinstance(path, str | Path):
                raise TypeError(f"path at index {i} must be str or Path, got {type(path).__name__}")
        return [Path(p).expanduser() for p in include]

    def _validate_settings(self, settings: object) -> dict[str, SettingsDict]:
        if not isinstance(settings, dict):
            raise TypeError(f"must be dict, got {type(settings).__name__}")
        new_settings: dict[str, SettingsDict] = {}
        for name, module_settings in settings.items():
            if not isinstance(name, str):
                raise TypeError(f"keys must be str, got {type(name).__name__}")
            name = name.strip()
            if not name:
                raise ValueError("keys must be non-empty")
            try:
                new_settings[name] = _ensure_settings_dict(module_settings)
            except (TypeError, ValueError) as exc:
                raise type(exc)(f"module {name!r}: {exc}") from exc
        return new_settings

    def _validate_modules(self, modules: object) -> list[ModuleDict]:
        if not isinstance(modules, list):
            raise TypeError(f"must be list, got {type(modules).__name__}")
        new_modules: list[ModuleDict] = []
        for i, module in enumerate(modules):
            try:
                new_modules.append(_ensure_module_dict(module))
            except (TypeError, ValueError) as exc:
                raise type(exc)(f"module at index {i}: {exc}") from exc
        return new_modules

    @cached_property
    def _modules_lookup(self) -> Mapping[ModuleKey, ModuleDict]:
        return {(m["name"], m.get("instance")): m for m in self.modules}

    def module_keys(self) -> Iterator[ModuleKey]:
        """Yield the configured module identifiers in order."""
        for module in self.modules:
            yield module["name"], module.get("instance")

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
    def from_file(cls, path: str | Path) -> Self:
        """Instantiate a configuration object from a toml file."""
        with open(path, "rb") as file:
            return cls(**tomllib.load(file))


def _ensure_env_dict(env: object) -> EnvDict:
    if not isinstance(env, dict):
        raise TypeError(f"`env` must be dict, got {type(env).__name__}")
    new_env: EnvDict = {}
    for key, value in env.items():
        if not isinstance(key, str):
            raise TypeError(f"keys must be str, got {type(key).__name__}")
        key = key.strip()
        if not key:
            raise ValueError("keys must be non-empty")
        if not isinstance(value, str):
            raise TypeError(f"value for key {key!r} must be str, got {type(value).__name__}")
        new_env[key] = value
    return new_env


def _ensure_settings_dict(settings: object) -> SettingsDict:
    if not isinstance(settings, dict):
        raise TypeError(f"must be dict, got {type(settings).__name__}")
    settings_new: SettingsDict = {}
    if (env := settings.get("env", MISSING)) is not MISSING:
        settings_new["env"] = _ensure_env_dict(env)
    if (on_click := settings.get("on_click", MISSING)) is not MISSING:
        settings_new["on_click"] = _ensure_on_click_dict(on_click)
    if (params := settings.get("params", MISSING)) is not MISSING:
        if not isinstance(params, dict):
            raise TypeError(f"`params` must be dict, got {type(params).__name__}")
        for key, value in params.items():
            if not isinstance(key, str):
                raise TypeError(f"keys must be str, got {type(key).__name__}")
        settings_new["params"] = params
    return settings_new


def _ensure_module_dict(module: object) -> ModuleDict:
    if not isinstance(module, dict):
        raise TypeError(f"must be dict, got {type(module).__name__}")
    if (name := module.get("name", MISSING)) is MISSING:
        raise ValueError("missing required key: `name`")
    if not isinstance(name, str):
        raise TypeError(f"module name must be str, got {type(name).__name__}")
    name = name.strip()
    if not name:
        raise ValueError("module name must be non-empty")
    new_module: ModuleDict = {"name": name}
    if (instance := module.get("instance", MISSING)) is not MISSING:
        if not isinstance(instance, str):
            raise TypeError(f"module instance must be str, got {type(instance).__name__}")
        if not instance:
            raise ValueError("module instance must be non-empty")
        new_module["instance"] = instance
    return new_module | _ensure_settings_dict(module)


def _ensure_on_click_dict(on_click: object) -> OnClickDict:
    if not isinstance(on_click, dict):
        raise TypeError(f"`on_click` must be dict, got {type(on_click).__name__}")
    on_click_new: OnClickDict = {}
    for button, command in on_click.items():
        try:
            button = int(button)
        except TypeError, ValueError:
            raise TypeError(f"buttons must be int, got {type(button).__name__}")
        if isinstance(command, list):
            for i, token in enumerate(command):
                if not isinstance(token, str):
                    raise TypeError(f"command word at index {i} must be str, got {type(token).__name__}")
        elif not isinstance(command, str):
            raise TypeError("command must be a str or list of str")
        on_click_new[button] = command
    return on_click_new


__all__ = [Config.__name__]
