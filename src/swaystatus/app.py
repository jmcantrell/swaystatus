"""The application manages the daemon's life cycle."""

import argparse
from functools import cached_property
from pathlib import Path

from .args import arg_parser
from .config import Config
from .context import context
from .daemon import Daemon
from .element import BaseElement
from .env import environ_path, environ_paths
from .logger import logger
from .modules import Registry

type Seconds = float | int


class App:
    """Manager of the daemon's life cycle."""

    @cached_property
    def args(self) -> argparse.Namespace:
        return arg_parser.parse_args()

    @cached_property
    def default_config_dir(self) -> Path:
        return (environ_path("XDG_CONFIG_HOME") or (Path.home() / ".config")) / "swaystatus"

    @cached_property
    def env_config_dir(self) -> Path | None:
        return environ_path("SWAYSTATUS_CONFIG_DIR")

    @cached_property
    def config_dir(self) -> Path:
        return self.args.config_dir or self.env_config_dir or self.default_config_dir

    @cached_property
    def default_config_file(self) -> Path:
        return self.config_dir / "config.toml"

    @cached_property
    def env_config_file(self) -> Path | None:
        return environ_path("SWAYSTATUS_CONFIG_FILE")

    @cached_property
    def config_file(self) -> Path:
        return self.args.config_file or self.env_config_file or self.default_config_file

    @cached_property
    def config(self) -> Config:
        with context("configuration"):
            logger.info("from file %r", str(self.config_file))
            config = Config.from_file(self.config_file)
            logger.debug("%r", config)
        return config

    @cached_property
    def interval(self) -> Seconds | None:
        return self.args.interval if self.args.interval is not None else self.config.interval

    @cached_property
    def click_events(self) -> bool:
        return self.args.click_events if self.args.click_events is not None else self.config.click_events

    @cached_property
    def env_package_path(self) -> list[Path]:
        return environ_paths("SWAYSTATUS_PACKAGE_PATH")

    @cached_property
    def default_data_dir(self) -> Path:
        return (environ_path("XDG_DATA_HOME") or (Path.home() / ".local/share")) / "swaystatus"

    @cached_property
    def env_data_dir(self) -> Path | None:
        return environ_path("SWAYSTATUS_DATA_DIR")

    @cached_property
    def data_dir(self) -> Path:
        return self.args.data_dir or self.env_data_dir or self.default_data_dir

    @cached_property
    def include(self) -> list[Path]:
        return [*self.args.include, *self.config.include, *self.env_package_path, self.data_dir / "modules"]

    @cached_property
    def registry(self) -> Registry:
        with context("registry"):
            logger.debug("include %r", self.include)
            registry = Registry(self.include)
            logger.debug("packages %r", registry)
        return registry

    @cached_property
    def elements(self) -> list[BaseElement]:
        elements = []
        for i, module in enumerate(self.config.modules_merged()):
            with context(f"element {i}"):
                logger.info("initializing from %s", module)
                logger.debug("%r", module)
                Element = self.registry.find(module.name)
                element = Element(
                    module.name,
                    instance=module.instance,
                    env=module.settings.env,
                    on_click=module.settings.on_click,
                    **module.settings.params,
                )
                logger.debug("%r", element)
            elements.append(element)
        return elements

    @cached_property
    def daemon(self) -> Daemon:
        return Daemon(self.elements, self.interval, self.click_events)

    def run(self) -> None:
        if self.args.log_level is not None:
            logger.setLevel(self.args.log_level)
        logger.info("daemon starting")
        self.daemon.start()
        self.daemon.join()
        logger.info("daemon finished")


__all__ = [App.__name__]
