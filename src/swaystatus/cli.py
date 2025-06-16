"""Generate a status line for swaybar."""

import argparse
import logging
from pathlib import Path

from .app import App
from .config import Config
from .daemon import Daemon
from .env import config_home, data_home, environ_path, environ_paths, self_name
from .logging import logger
from .version import version


def configure_logging(level: str) -> None:
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter("%(name)s: %(levelname)s: %(message)s"))
    logging.basicConfig(level=level.upper(), handlers=[stream_handler])


def load_config(args: argparse.Namespace) -> Config:
    data_dir: Path = args.data_dir or environ_path("SWAYSTATUS_DATA_DIR") or (data_home / self_name)
    config_dir: Path = args.config_dir or environ_path("SWAYSTATUS_CONFIG_DIR") or (config_home / self_name)
    config_file: Path = args.config_file or environ_path("SWAYSTATUS_CONFIG_FILE") or (config_dir / "config.toml")
    config = Config.from_file(config_file) if config_file.is_file() else Config()
    include = []
    if args.include:
        include.extend(args.include)
    if config.include:
        include.extend(config.include)
    if paths := environ_paths("SWAYSTATUS_PACKAGE_PATH"):
        include.extend(paths)
    include.append(data_dir / "modules")
    config.include = include
    if args.order:
        config.order = args.order
    if args.interval:
        config.interval = args.interval
    if args.click_events:
        config.click_events = True
    return config


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
        version=version(),
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
        action="append",
        metavar="DIRECTORY",
        type=Path,
        help="include an additional element package",
    )
    parser.add_argument(
        "-i",
        "--interval",
        type=float,
        metavar="SECONDS",
        help="override default update interval",
    )
    parser.add_argument(
        "--click-events",
        dest="click_events",
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


def main() -> int:
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
        return 1
    return 0


__all__ = [main.__name__]
