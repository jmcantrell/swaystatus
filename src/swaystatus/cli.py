"""Generates a status line for swaybar"""

import os, sys
from logging import Formatter, StreamHandler, FileHandler
from pathlib import Path
from argparse import ArgumentParser
from .loop import run
from .config import Config
from .modules import Modules
from .logging import logger

me = os.path.basename(sys.argv[0])
log_formatter = Formatter("%(levelname)s: %(message)s")
config_home = Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser()

try:
    from systemd.journal import JournalHandler
except ModuleNotFoundError:
    journal_available = False
else:
    journal_available = True


def environ_path(name, default=None):
    value = os.environ.get(name, default)
    return Path(value).expanduser() if value else default


def environ_paths(name):
    value = os.environ.get(name)
    parts = value.split(":") if value else []
    return [Path(p).expanduser() for p in parts]


def add_log_handler(handler):
    handler.setFormatter(log_formatter)
    logger.addHandler(handler)


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
        help="include additional module package",
    )

    p.add_argument(
        "-i",
        "--interval",
        type=float,
        metavar="SECONDS",
        help="specify interval between updates",
    )

    p.add_argument(
        "--no-click-events",
        dest="click_events",
        action="store_false",
        help="disable click events",
    )

    p.add_argument(
        "-l",
        "--log-file",
        metavar="FILE",
        help="output logging to %(metavar)s (default: stderr)",
    )

    if journal_available:
        p.add_argument(
            "-j",
            "--log-journal",
            action="store_true",
            help="output logging to systemd journal",
        )

    return p.parse_args()


def main():
    args = parse_args()

    config_dir = args.config_dir or environ_path(
        "SWAYSTATUS_CONFIG_DIR", config_home / me
    )
    config_file = args.config_file or environ_path(
        "SWAYSTATUS_CONFIG_FILE", config_dir / "config.toml"
    )

    config = Config()
    config.read_file(config_file)

    add_log_handler(StreamHandler())

    if args.log_file:
        add_log_handler(FileHandler(args.log_file))

    if args.log_journal:
        add_log_handler(JournalHandler(SYSLOG_IDENTIFIER=logger.name))

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

    elements = []
    modules = Modules(config["include"])
    settings = config.get("settings", {})

    for module_id in config.get("order", []):
        module_name = module_id.split(":", maxsplit=1)[0]
        element_settings = settings.get(module_name, {}).copy()
        element_settings.update(settings.get(module_id, {}))
        element = modules.find(module_name).Element(**element_settings)
        element.name = module_id
        elements.append(element)

    try:
        run(elements, **config)
    except Exception:
        logger.exception("unhandled exception in main loop")
        sys.exit(1)
