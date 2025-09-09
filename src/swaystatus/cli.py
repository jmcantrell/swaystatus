"""Generate a status line for swaybar."""

import argparse
from pathlib import Path

from .app import App
from .config import Config
from .daemon import Daemon
from .env import environ_path, environ_paths, self_name
from .logging import configure as configure_logging
from .logging import logger
from .version import version
from .xdg import config_home, data_home


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=lambda prog: argparse.RawDescriptionHelpFormatter(
            prog, indent_increment=4, max_help_position=45
        ),
        epilog="See `pydoc swaystatus` for full documentation.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=version,
    )
    parser.add_argument(
        "-c",
        "--config-file",
        metavar="FILE",
        type=Path,
        help="override configuration file",
    )
    parser.add_argument(
        "-C",
        "--config-dir",
        metavar="DIRECTORY",
        type=Path,
        help="override configuration directory",
    )
    parser.add_argument(
        "-D",
        "--data-dir",
        metavar="DIRECTORY",
        type=Path,
        help="override data directory",
    )
    parser.add_argument(
        "-I",
        "--include",
        metavar="DIRECTORY",
        type=Path,
        action="append",
        default=[],
        help="include an additional element package",
    )
    parser.add_argument(
        "-i",
        "--interval",
        metavar="SECONDS",
        type=float,
        help="override default update interval",
    )
    parser.add_argument(
        "--click-events",
        action="store_true",
        help="enable click events",
    )
    parser.add_argument(
        "--log-level",
        metavar="LEVEL",
        default="warning",
        choices=["debug", "info", "warning", "error", "critical"],
        help="override default minimum logging level (default: %(default)s)",
    )
    parser.add_argument(
        "order",
        metavar="NAME[:INSTANCE]",
        nargs="*",
        help="override configured element order",
    )
    return parser.parse_args()


def load_config(args: argparse.Namespace) -> Config:
    config_dir = environ_path("SWAYSTATUS_CONFIG_DIR") or args.config_dir or (config_home / self_name)
    config_file = environ_path("SWAYSTATUS_CONFIG_FILE") or args.config_file or (config_dir / "config.toml")
    config = Config.from_file(config_file) if config_file.is_file() else Config()
    data_dir = environ_path("SWAYSTATUS_DATA_DIR") or (data_home / self_name)
    package_path = environ_paths("SWAYSTATUS_PACKAGE_PATH") + [data_dir / "modules"]
    config.include = args.include + config.include + package_path
    if args.order:
        config.order = args.order
    if args.interval:
        config.interval = args.interval
    if args.click_events:
        config.click_events = True
    return config


def main() -> None:
    args = parse_args()
    config = load_config(args)
    configure_logging(args.log_level)
    daemon = Daemon(
        config.elements,
        config.interval,
        config.click_events,
    )
    try:
        App(daemon).run()
    except Exception:
        logger.exception("unhandled exception in main")


__all__ = [main.__name__]
