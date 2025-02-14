"""Generate a status line for swaybar."""

import toml
import logging

from argparse import ArgumentParser, RawDescriptionHelpFormatter
from pathlib import Path

from .config import config
from .env import bin_name, config_home, environ_path, environ_paths
from .logging import logger
from .loop import start
from .modules import Modules


def configure_logging(level: str | int):
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter("%(name)s: %(levelname)s: %(message)s"))

    if level and isinstance(level, str):
        level = level.upper()

    logging.basicConfig(level=level, handlers=[stream_handler])


def parse_args():
    class MyHelpFormatter(RawDescriptionHelpFormatter):

        def __init__(self, *args, **kwargs):
            super().__init__(*args, max_help_position=40, indent_increment=4, **kwargs)

    parser = ArgumentParser(
        description=__doc__,
        usage="%(prog)s [OPTIONS]",
        formatter_class=MyHelpFormatter,
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
    config_dir = args.config_dir or environ_path(
        "SWAYSTATUS_CONFIG_DIR", config_home / bin_name
    )
    config_file = args.config_file or environ_path(
        "SWAYSTATUS_CONFIG_FILE", config_dir / "config.toml"
    )

    if config_file.is_file():
        config.update(toml.loads(open(config_file).read()))

    config["include"] = (
        (args.include or [])
        + [config_dir / "modules"]
        + [Path(d).expanduser() for d in config.get("include", [])]
        + environ_paths("SWAYSTATUS_MODULE_PATH")
    )

    if args.interval:
        config["interval"] = args.interval

    if not args.click_events:
        config["click_events"] = False

    return config


def deep_merge_dicts(first, second):
    """
    Recursively merge the second dictionary into the first.
    """
    result = first.copy()
    for key, value in second.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def load_elements(order, include, settings):
    elements = []
    modules = Modules(include)

    for key in order:
        try:
            name, instance = key.split(":", maxsplit=1)
        except ValueError:
            name, instance = key, None

        module = modules.find(name)

        kwargs = deep_merge_dicts(
            settings.get(name, {}),
            settings.get(key, {}),
        )

        kwargs.update({"name": name, "instance": instance})

        logger.info(f"Loaded module from file: {module.__file__}")
        logger.debug(f"Initializing module: {kwargs!r}")

        elements.append(module.Element(**kwargs))

    return elements


def main():
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
