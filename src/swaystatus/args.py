import argparse
import logging
from pathlib import Path

from . import __version__

arg_parser = argparse.ArgumentParser(
    description="Generate a status line for swaybar",
    epilog="See `pydoc swaystatus` for full documentation.",
)
arg_parser.add_argument(
    "-v",
    "--version",
    action="version",
    version=__version__,
)
arg_parser.add_argument(
    "-c",
    "--config-file",
    metavar="FILE",
    type=Path,
    help="override configuration file",
)
arg_parser.add_argument(
    "-C",
    "--config-dir",
    metavar="DIRECTORY",
    type=Path,
    help="override configuration directory",
)
arg_parser.add_argument(
    "-D",
    "--data-dir",
    metavar="DIRECTORY",
    type=Path,
    help="override data directory",
)
arg_parser.add_argument(
    "-I",
    "--include",
    metavar="DIRECTORY",
    type=Path,
    action="append",
    default=[],
    help="include an additional element package",
)
arg_parser.add_argument(
    "-i",
    "--interval",
    metavar="SECONDS",
    type=float,
    help="override default update interval",
)
arg_parser.add_argument(
    "--click-events",
    action="store_true",
    help="enable click events",
)
arg_parser.add_argument(
    "--log-level",
    metavar="LEVEL",
    type=str.upper,
    default=logging.getLevelName(logging.root.level),
    choices=list(logging.getLevelNamesMapping().keys()),
    help="override default minimum logging level (default: %(default)s)",
)
