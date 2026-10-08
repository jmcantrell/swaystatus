"""The application manages runtime execution."""

from functools import cached_property
from pathlib import Path

from .args import Args
from .config import Config
from .context import context
from .daemon import Daemon
from .element import BaseElement
from .env import environ_path, environ_paths
from .logger import logger, logger_level_at
from .modules import Registry
from .xdg import xdg_config_home, xdg_data_home


class App:
    """Manager of runtime execution."""

    @cached_property
    def args(self) -> Args:
        """Parsed command line arguments."""
        return Args.parse()

    @cached_property
    def config_dir(self) -> Path:
        """
        Directory to load configuration files from.

        The directory used is one of the following (in order of preference):

            1. --config-dir=<DIRECTORY>

            2. $SWAYSTATUS_CONFIG_DIR

            3. $XDG_CONFIG_HOME/swaystatus/

            4. $HOME/.config/swaystatus/
        """

        return self.args.config_dir or environ_path("SWAYSTATUS_CONFIG_DIR") or xdg_config_home() / "swaystatus"

    @cached_property
    def config_file(self) -> Path:
        """
        File to load runtime configuration from.

        The file used is one of the following (in order of preference):

            1. --config-file=<FILE>

            2. $SWAYSTATUS_CONFIG_FILE

            3. <DIRECTORY>/config.toml where <DIRECTORY> is from --config-dir=<DIRECTORY>

            4. $SWAYSTATUS_CONFIG_DIR/config.toml

            5. $XDG_CONFIG_HOME/swaystatus/config.toml

            6. $HOME/.config/swaystatus/config.toml
        """

        return self.args.config_file or environ_path("SWAYSTATUS_CONFIG_FILE") or self.config_dir / "config.toml"

    @cached_property
    def config(self) -> Config:
        """Parsed and validated application configuration."""
        with context("configuration"):
            logger.info("from file %r", str(self.config_file))
            config = Config.from_file(self.config_file)
            logger.debug("%r", config)
        return config

    @cached_property
    def data_dir(self) -> Path:
        """
        Directory to load application data from.

        The directory used is one of the following (in order of preference):

            1. --data-dir=<DIRECTORY>

            2. $SWAYSTATUS_DATA_DIR

            3. $XDG_DATA_HOME/swaystatus/

            4. $HOME/.local/share/swaystatus/
        """

        return self.args.data_dir or environ_path("SWAYSTATUS_DATA_DIR") or xdg_data_home() / "swaystatus"

    @cached_property
    def include(self) -> list[Path]:
        """
        Module package directores to search for status bar modules.

        The list is populated from the following sources (in order of preference):

            1. --include=<DIRECTORY> (can be used multiple times)

            2. Directories included in the configuration file:

                include = ['/path/to/package1', '/path/to/package2']

            3. Python packages in a colon-separated environment variable:

                SWAYSTATUS_PACKAGE_PATH="/path/to/package1:/path/to/package2"

            4. A 'modules' python package in the data directory

            5. Installed python packages configured with a "swaystatus.modules"
               entry point like the following:

                [project.entry-points."swaystatus.modules"]
                package = "awesome_swaystatus_modules"

        If a directory does not exist or does not look like a python package,
        it will be ignored.
        """

        return [
            *self.args.include,
            *self.config.include,
            *environ_paths("SWAYSTATUS_PACKAGE_PATH"),
            self.data_dir / "modules",
        ]

    @cached_property
    def registry(self) -> Registry:
        """Loader for module packages and their elements."""
        with context("registry"):
            logger.debug("include %r", self.include)
            registry = Registry(self.include)
            logger.debug("packages %r", registry)
        return registry

    @cached_property
    def elements(self) -> list[BaseElement]:
        """Status bar content producers, loaded and initialized."""
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
        """Coordinator for input and output."""
        return Daemon(self.elements, self.config.interval, self.config.click_events)

    def run(self) -> None:
        """Start the daemon and wait for it to be shut down."""
        with logger_level_at(self.args.log_level):
            logger.info("daemon starting")
            self.daemon.start()
            self.daemon.join()
            logger.info("daemon stopped")


__all__ = [App.__name__]
