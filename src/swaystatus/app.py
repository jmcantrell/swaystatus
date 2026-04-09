"""The application manages the daemon's life cycle."""

import argparse
from contextlib import suppress
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


class App:
    """Manager of the daemon's life cycle."""

    @cached_property
    def args(self) -> argparse.Namespace:
        return arg_parser.parse_args()

    @cached_property
    def config_home(self) -> Path:
        with suppress(KeyError):
            return environ_path("XDG_CONFIG_HOME")
        return Path.home() / ".config"

    @cached_property
    def config_dir(self) -> Path:
        with suppress(AttributeError):
            return self.args.config_dir
        with suppress(KeyError):
            return environ_path("SWAYSTATUS_CONFIG_DIR")
        return self.config_home / "swaystatus"

    @cached_property
    def config_file(self) -> Path:
        with suppress(AttributeError):
            return self.args.config_file
        with suppress(KeyError):
            return environ_path("SWAYSTATUS_CONFIG_FILE")
        return self.config_dir / "config.toml"

    @cached_property
    def config(self) -> Config:
        with context("configuration"):
            logger.info("from file %r", str(self.config_file))
            config = Config.from_file(self.config_file)
            logger.debug("%r", config)
        return config

    @cached_property
    def data_home(self) -> Path:
        with suppress(KeyError):
            return environ_path("XDG_DATA_HOME")
        return Path.home() / ".local/share"

    @cached_property
    def data_dir(self) -> Path:
        with suppress(AttributeError):
            return self.args.data_dir
        with suppress(KeyError):
            return environ_path("SWAYSTATUS_DATA_DIR")
        return self.data_home / "swaystatus"

    @cached_property
    def include(self) -> list[Path]:
        paths = []
        with suppress(AttributeError):
            paths.extend(self.args.include)
        paths.extend(self.config.include)
        with suppress(KeyError):
            paths.extend(environ_paths("SWAYSTATUS_PACKAGE_PATH"))
        paths.append(self.data_dir / "modules")
        return paths

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
        return Daemon(self.elements, self.config.interval, self.config.click_events)

    def run(self) -> None:
        with suppress(AttributeError):
            logger.setLevel(self.args.log_level)
        logger.info("daemon starting")
        self.daemon.start()
        self.daemon.join()
        logger.info("daemon finished")


__all__ = [App.__name__]
