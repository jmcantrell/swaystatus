"""Generate a status line for swaybar."""

import argparse
import logging
import tomllib
from pathlib import Path
from typing import Iterable

from .config import config
from .element import BaseElement
from .env import bin_name, config_home, environ_path, environ_paths
from .logging import logger
from .loop import start
from .modules import Modules


def configure_logging(level: str) -> None:
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter("%(name)s: %(levelname)s: %(message)s"))
    logging.basicConfig(level=level.upper(), handlers=[stream_handler])


def parse_args() -> argparse.Namespace:
    class MyHelpFormatter(argparse.RawDescriptionHelpFormatter):
        def __init__(self, prog) -> None:
            super().__init__(prog, indent_increment=4, max_help_position=30)

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=MyHelpFormatter)
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
        "-I",
        "--include",
        action="append",
        metavar="DIRECTORY",
        type=Path,
        help="include additional modules package",
    )
    parser.add_argument(
        "-i",
        "--interval",
        type=float,
        metavar="SECONDS",
        help="override default update interval",
    )
    parser.add_argument(
        "--no-click-events",
        dest="click_events",
        action="store_false",
        help="disable click events",
    )
    parser.add_argument(
        "--log-level",
        metavar="LEVEL",
        default="info",
        choices=["debug", "info", "warning", "error", "critical"],
        help="override default minimum logging level (default: %(default)s)",
    )
    return parser.parse_args()


def parse_config(args):
    config_dir = args.config_dir or environ_path("SWAYSTATUS_CONFIG_DIR") or config_home / bin_name
    config_file = args.config_file or environ_path("SWAYSTATUS_CONFIG_FILE") or config_dir / "config.toml"

    if config_file.is_file():
        config.update(tomllib.loads(open(config_file).read()))

    config["include"] = (
        (args.include or [])
        + [config_dir / "modules"]
        + [Path(d).expanduser() for d in config.get("include", [])]
        + (environ_paths("SWAYSTATUS_MODULE_PATH") or [])
    )

    if args.interval:
        config["interval"] = args.interval

    if not args.click_events:
        config["click_events"] = False

    return config


def deep_merge_dicts(first: dict, second: dict) -> dict:
    """Recursively merge the second dictionary into the first."""
    result = first.copy()
    for key, value in second.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def load_elements(order: Iterable[str], include: Iterable[Path], settings: dict) -> list[BaseElement]:
    elements = []
    modules = Modules(include)

    for key in order:
        try:
            name, instance = key.split(":", maxsplit=1)
        except ValueError:
            name, instance = key, None

        module = modules.find(name)
        logger.info(f"Loaded module from file: {module.__file__}")

        kwargs = deep_merge_dicts(settings.get(name, {}), settings.get(key, {}))
        kwargs.update({"name": name, "instance": instance})

        logger.debug(f"Initializing module: {kwargs!r}")
        elements.append(module.Element(**kwargs))

    return elements


def main() -> int:
    args = parse_args()
    configure_logging(args.log_level)

    config = parse_config(args)
    logger.debug(f"Using configuration: {config!r}")

    elements = load_elements(
        config["order"],
        config["include"],
        config["settings"],
    )

    try:
        start(
            elements,
            config["interval"],
            config["click_events"],
        )
    except Exception:
        logger.exception("Unhandled exception in main loop")
        return 1
    return 0
