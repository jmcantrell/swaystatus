"""Generate a status line for swaybar."""

import sys
import toml
from pathlib import Path
from argparse import ArgumentParser
from .loop import start
from .config import config
from .modules import Modules
from .logging import logger, configure as configure_logging
from .env import bin_name, config_home, environ_path, environ_paths


def parse_args():
    p = ArgumentParser(description=__doc__)

    p.add_argument(
        "-c",
        "--config-file",
        metavar="FILE",
        type=Path,
        help="override configuration file",
    )

    p.add_argument(
        "-C",
        "--config-dir",
        metavar="DIRECTORY",
        type=Path,
        help="override configuration directory",
    )

    p.add_argument(
        "-I",
        "--include",
        action="append",
        metavar="DIRECTORY",
        type=Path,
        help="include additional modules package",
    )

    p.add_argument(
        "-i",
        "--interval",
        type=float,
        metavar="SECONDS",
        help="override default update interval",
    )

    p.add_argument(
        "--no-click-events",
        dest="click_events",
        action="store_false",
        help="disable click events",
    )

    p.add_argument(
        "-L",
        "--log-level",
        metavar="LEVEL",
        choices=["debug", "info", "warning", "error", "critical"],
        help="override default logging minimum severity level",
    )

    p.add_argument(
        "-l",
        "--log-file",
        metavar="FILE",
        type=Path,
        help="output logging to %(metavar)s",
    )

    p.add_argument(
        "--syslog",
        action="store_true",
        help="output logging to syslog",
    )

    return p.parse_args()


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


def load_elements(order, include, settings):
    elements = []
    modules = Modules(include)

    for key in order:
        ids = key.split(":", maxsplit=1)
        ids.append(None)

        name, instance = ids[:2]

        module = modules.find(name)

        element_settings = {"name": name, "instance": instance}
        element_settings.update(settings.get(name, {}).copy())
        element_settings.update(settings.get(key, {}).copy())

        logger.info(f"Loaded module from file: {module.__file__}")
        logger.debug(f"Initializing module: {element_settings!r}")

        elements.append(module.Element(**element_settings))

    return elements


def main():
    args = parse_args()

    configure_logging(level=args.log_level, file=args.log_file, syslog=args.syslog)

    config = parse_config(args)
    logger.debug(f"Using configuration: {config!r}")

    elements = load_elements(config["order"], config["include"], config["settings"])

    try:
        start(elements, config["interval"], config["click_events"])
    except Exception:
        logger.exception("Unhandled exception in main loop")
        sys.exit(1)
