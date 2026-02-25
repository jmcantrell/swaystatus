"""
Runtime configuration.

Configuration is defined in one of the following TOML files (in order of preference):

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
        Settings for all modules of the same name.

    `modules` (type: list[dict], default: [])
        The modules to be displayed in the status line.

Each item in the `modules` list recognizes the following keys:

    `name` (type: str, required)
        Specify the module to be loaded.

    `instance` (type: str | None, default: None)
        Differentiate this module from others of the same `name`.

    `settings` (type: dict | None, default: None)
        Settings for this module only.

Each `settings[name]` and `modules[i].settings` dict recognizes the following keys:

    `on_click` (type: dict[int, str | list[str]], default: {})
        Shell commands to run when the element is clicked by pointer buttons.

    `env` (type: dict[str, str], default: {})
        Environment changes to make during click handler execution.

    `params` (type: dict[str, Any], default: {})
        Extra keyword parameters passed to the element initializer.
"""

import tomllib
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from os import PathLike
from pathlib import Path
from typing import Self

from .paths import path_normalized

type Seconds = float | int
type EnvMapping = Mapping[str, str | None]
type OnClickMapping = Mapping[int, str | Sequence[str] | None]
type ParamsMapping = Mapping[str, object]


@dataclass(slots=True, kw_only=True)
class ModuleSettings:
    env: EnvMapping = field(default_factory=dict)
    on_click: OnClickMapping = field(default_factory=dict)
    params: ParamsMapping = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._validate_env()
        self._validate_on_click()
        self._validate_params()

    def _validate_env(self) -> None:
        if not isinstance(self.env, dict):
            raise TypeError(f"`env` must be dict, got {type(self.env).__name__}")
        for key, value in self.env.items():
            if not isinstance(key, str):
                raise TypeError(f"`env` keys must be str, got {type(key).__name__}")
            if not key.strip():
                raise ValueError("`env` keys must be non-empty")
            if value is not None and not isinstance(value, str):
                raise TypeError(f"`env[{key!r}]` must be str, got {type(value).__name__}")

    def _validate_on_click(self) -> None:
        if not isinstance(self.on_click, dict):
            raise TypeError(f"`on_click` must be dict, got {type(self.on_click).__name__}")
        for button, command in self.on_click.items():
            if not isinstance(button, int):
                raise TypeError(f"`on_click` keys must be int, got {type(button).__name__}")
            if command is not None:
                if isinstance(command, list):
                    for i, token in enumerate(command):
                        if not isinstance(token, str):
                            raise TypeError(f"`on_click[{button!r}][{i}]` must be str, got {type(token).__name__}")
                        if not token.strip():
                            raise ValueError(f"`on_click[{button!r}][{i}] must be non-empty")
                elif isinstance(command, str):
                    if not command.strip():
                        raise ValueError(f"`on_click[{button!r}] must be non-empty")
                else:
                    raise TypeError(f"`on_click[{button!r}] must be a str or list of str, got {type(command).__name__}")

    def _validate_params(self) -> None:
        if not isinstance(self.params, dict):
            raise TypeError(f"must be dict, got {type(self.params).__name__}")
        for key in self.params:
            if not isinstance(key, str):
                raise TypeError(f"`params` keys must be str, got {type(key).__name__}")
            if not key.strip():
                raise ValueError("`params` keys must be non-empty")

    @classmethod
    def parse(cls, data: dict) -> Self:
        """Create a module settings object from a dictionary representation."""
        if (on_click := data.get("on_click")) and isinstance(on_click, dict):
            data["on_click"] = {int(k): v for k, v in on_click.items()}
        return cls(**data)


@dataclass(slots=True, kw_only=True)
class Module:
    name: str
    instance: str | None = None
    settings: ModuleSettings = field(default_factory=ModuleSettings)

    def __post_init__(self) -> None:
        self._validate_name()
        self._validate_instance()
        self._validate_settings()

    def __str__(self) -> str:
        return f"module name={self.name!r} instance={self.instance!r}"

    def _validate_name(self) -> None:
        if not isinstance(self.name, str):
            raise TypeError(f"`name` must be str, got {type(self.name).__name__}")
        if not self.name.strip():
            raise ValueError("`name` must be non-empty")

    def _validate_instance(self) -> None:
        if self.instance is not None:
            if not isinstance(self.instance, str):
                raise TypeError(f"`instance` must be str, got {type(self.instance).__name__}")
            if not self.instance.strip():
                raise ValueError("`instance` must be non-empty, if set")

    def _validate_settings(self) -> None:
        if not isinstance(self.settings, ModuleSettings):
            raise TypeError(f"`settings` must be Settings, got {type(self.settings).__name__}")

    @classmethod
    def parse(cls, data: dict) -> Self:
        """Create a module object from a dictionary representation."""
        if (settings := data.get("settings")) and isinstance(settings, dict):
            data["settings"] = ModuleSettings.parse(settings)
        return cls(**data)


@dataclass(slots=True, kw_only=True)
class Config:
    """Data class representing runtime configuration."""

    interval: Seconds | None = None
    click_events: bool = False
    env: EnvMapping = field(default_factory=dict)
    include: Sequence[Path] = field(default_factory=list)
    settings: Mapping[str, ModuleSettings] = field(default_factory=dict)
    modules: Sequence[Module] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._validate_interval()
        self._validate_click_events()
        self._validate_env()
        self._validate_include()
        self._validate_settings()
        self._validate_modules()

    def _validate_interval(self) -> None:
        if self.interval is not None:
            if not isinstance(self.interval, float | int):
                raise TypeError(f"`interval` must be float or int, got {type(self.interval).__name__}")
            if self.interval <= 0:
                raise ValueError("`interval` must be greater than zero")

    def _validate_click_events(self) -> None:
        if not isinstance(self.click_events, bool):
            raise TypeError(f"`click_events` must be bool, got {type(self.click_events).__name__}")

    def _validate_env(self) -> None:
        if not isinstance(self.env, dict):
            raise TypeError(f"`env` must be dict, got {type(self.env).__name__}")
        for key, value in self.env.items():
            if not isinstance(key, str):
                raise TypeError(f"`env` keys must be str, got {type(key).__name__}")
            if not key.strip():
                raise ValueError("`env` keys must be non-empty")
            if value is not None and not isinstance(value, str):
                raise TypeError(f"`env[{key!r}]` must be str, got {type(value).__name__}")

    def _validate_include(self) -> None:
        if not isinstance(self.include, list):
            raise TypeError(f"`include` must be list, got {type(self.include).__name__}")
        for i, path in enumerate(self.include):
            if not isinstance(path, Path):
                raise TypeError(f"`include[{i!r}]` must be Path, got {type(path).__name__}")
            if not path.is_absolute():
                raise ValueError(f"`include[{i!r}]` must be an absolute path")

    def _validate_settings(self) -> None:
        if not isinstance(self.settings, dict):
            raise TypeError(f"`settings` must be dict, got {type(self.settings).__name__}")
        for key, module_settings in self.settings.items():
            if not isinstance(key, str):
                raise TypeError(f"`settings` keys must be str, got {type(key).__name__}")
            if not key.strip():
                raise ValueError("`settings` keys must be non-empty")
            if not isinstance(module_settings, ModuleSettings):
                raise TypeError(f"`settings[{key!r}]` must be Settings, got {type(module_settings).__name__}")

    def _validate_modules(self) -> None:
        if not isinstance(self.modules, list):
            raise TypeError(f"`modules` must be list, got {type(self.modules).__name__}")
        for i, module in enumerate(self.modules):
            if not isinstance(module, Module):
                raise TypeError(f"`modules[{i!r}]` must be Module, got {type(module).__name__}")

    def modules_merged(self) -> Iterator[Module]:
        empty_settings = ModuleSettings()
        for module in self.modules:
            settings = self.settings.get(module.name, empty_settings)
            yield Module(
                name=module.name,
                instance=module.instance,
                settings=ModuleSettings(
                    env={**self.env, **settings.env, **module.settings.env},
                    on_click={**settings.on_click, **module.settings.on_click},
                    params={**settings.params, **module.settings.params},
                ),
            )

    @classmethod
    def parse(cls, data: dict) -> Self:
        """Create a configuration object from a dictionary representation."""
        if (include := data.get("include")) and isinstance(include, list):
            data["include"] = [path_normalized(d) for d in include]
        if (settings := data.get("settings")) and isinstance(settings, dict):
            data["settings"] = {k: ModuleSettings.parse(v) if isinstance(v, dict) else v for k, v in settings.items()}
        if (modules := data.get("modules")) and isinstance(modules, list):
            data["modules"] = [Module.parse(m) if isinstance(m, dict) else m for m in modules]
        return cls(**data)

    @classmethod
    def from_file(cls, path: str | PathLike[str]) -> Self:
        """Instantiate a configuration object from a TOML file."""
        with open(path, "rb") as file:
            return cls.parse(tomllib.load(file))


__all__ = [
    Config.__name__,
    Module.__name__,
    ModuleSettings.__name__,
]
