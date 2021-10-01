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

    config = Config()
    config.read_file(config_file)

    config["include"] = (
        (args.include or [])
        + [config_dir / "modules"]
        + config.get("include", [])
    )

    if args.interval:
        config["interval"] = args.interval

    if not args.click_events:
        config["click_events"] = False

    elements = []
    modules = Modules(config["include"])
    settings = config.get("settings", {})

    for module_id in config.get("order", []):
        name = module_id.split(":", maxsplit=1)[0]
        element = modules.find(name).Element(**settings.get(module_id, {}))
        element.name = module_id
        elements.append(element)

    run(elements, **config)
