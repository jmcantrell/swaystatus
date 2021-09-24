"""Generates a status line for swaybar"""

import os
import sys
from pathlib import Path
from argparse import ArgumentParser
from .loop import run
from .config import Config
from .modules import Modules


def parse_args():
    p = ArgumentParser(description=__doc__)

    p.add_argument(
        "-c",
        "--config-file",
        metavar="FILE",
        help="specify configuration file",
    )

    p.add_argument(
        "-C",
        "--config-dir",
        metavar="DIRECTORY",
        help="specify configuration directory",
    )

    p.add_argument(
        "-I",
        "--include",
        action="append",
        metavar="DIRECTORY",
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

    return p.parse_args()


def main():
    args = parse_args()

    config_dir = args.config_dir or (
        Path(os.environ.get("XDG_CONFIG_HOME", Path("~/.config").expanduser()))
        / os.path.basename(sys.argv[0])
    )

    config_file = args.config_file or (config_dir / "config.toml")

    config = Config(config_file)
    modules = Modules((args.include or []) + config.include)

    elements = []

    for module_name in config.order:
        module = modules.find(module_name)
        element = module.Element(**config.settings.get(module_name, {}))
        element.name = module_name
        elements.append(element)

    options = {
        "interval": config.interval,
        "click_events": config.click_events,
    }

    if args.interval:
        options["interval"] = args.interval

    if not args.click_events:
        options["click_events"] = False

    run(elements, **options)
