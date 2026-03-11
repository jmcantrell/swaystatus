import argparse
from typing import Iterator

from .app import App
from .args import arg_parser
from .config import Config
from .daemon import Daemon
from .element import BaseElement
from .env import environ_path, environ_paths, self_name
from .logging import configure_logging, logger
from .modules import PackageRegistry
from .status_line import StatusLine
from .xdg import config_home, data_home

env_config_dir = environ_path("SWAYSTATUS_CONFIG_DIR")
env_config_file = environ_path("SWAYSTATUS_CONFIG_FILE")
env_data_dir = environ_path("SWAYSTATUS_DATA_DIR")
env_package_path = environ_paths("SWAYSTATUS_PACKAGE_PATH")


def load_config(args: argparse.Namespace) -> Config:
    config_dir = env_config_dir or args.config_dir or (config_home / self_name)
    config_file = env_config_file or args.config_file or (config_dir / "config.toml")
    modules_dir = (env_data_dir or args.data_dir or (data_home / self_name)) / "modules"
    config = Config.from_file(config_file) if config_file.is_file() else Config()
    config.include = args.include + config.include + env_package_path + [modules_dir]
    if args.interval:
        config.interval = args.interval
    if args.click_events:
        config.click_events = True
    return config


def load_elements(config: Config) -> Iterator[BaseElement]:
    package_registry = PackageRegistry(config.include)
    for name, instance in config.module_keys():
        kwargs = config.module(name, instance)
        logger.debug("loading element name=%r instance=%r: %r", name, instance, kwargs)
        yield package_registry.module(name)(name, instance, **kwargs)


def main() -> None:
    args = arg_parser.parse_args()
    config = load_config(args)
    configure_logging(args.log_level)
    status_line = StatusLine(list(load_elements(config)))
    daemon = Daemon(status_line, config.interval, config.click_events)
    try:
        App(daemon).run()
    except Exception:
        logger.exception("unhandled exception in app")
