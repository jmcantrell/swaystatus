import argparse
from pathlib import Path
from typing import Iterator

from .app import App
from .args import arg_parser
from .config import Config
from .daemon import Daemon
from .element import BaseElement
from .env import environ_path, environ_paths
from .logging import logger
from .modules import PackageRegistry
from .status_line import StatusLine

self_name = "swaystatus"


def parse_args() -> argparse.Namespace:
    args = arg_parser.parse_args()
    logger.setLevel(args.log_level)
    return args


def load_config(args: argparse.Namespace) -> Config:
    xdg_config_home = environ_path("XDG_CONFIG_HOME")
    default_config_dir = (xdg_config_home or (Path.home() / ".config")) / self_name
    self_config_dir = environ_path("SWAYSTATUS_CONFIG_DIR")
    config_dir = args.config_dir or self_config_dir or default_config_dir
    self_config_file = environ_path("SWAYSTATUS_CONFIG_FILE")
    default_config_file = config_dir / "config.toml"
    config_file = args.config_file or self_config_file or default_config_file
    if config_file.is_file():
        logger.debug("loading configuration from file: %r", str(config_file))
        return Config.from_file(config_file)
    return Config()


def build_elements(args: argparse.Namespace, config: Config) -> Iterator[BaseElement]:
    xdg_data_home = environ_path("XDG_DATA_HOME")
    default_data_dir = (xdg_data_home or Path.home() / ".local/share") / self_name
    self_data_dir = environ_path("SWAYSTATUS_DATA_DIR")
    self_package_path = environ_paths("SWAYSTATUS_PACKAGE_PATH")
    data_dir = args.data_dir or self_data_dir or default_data_dir
    include = [*args.include, *config.include, *self_package_path, data_dir / "modules"]
    package_registry = PackageRegistry(include)
    for name, instance in config.module_keys():
        kwargs = config.module(name, instance)
        logger.debug("building element name=%r instance=%r: %r", name, instance, kwargs)
        yield package_registry.module(name)(name, instance, **kwargs)


def create_app() -> App:
    args = parse_args()
    config = load_config(args)
    status_line = StatusLine(list(build_elements(args, config)))
    return App(Daemon(status_line, config.interval, config.click_events))


def main() -> None:
    try:
        create_app().start()
    except Exception:
        logger.exception("unhandled exception in main")
        raise SystemExit(1)
