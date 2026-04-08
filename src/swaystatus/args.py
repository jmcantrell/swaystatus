"""Command-line interface argument parsing."""

import argparse
import logging

from . import __version__
from .paths import path_normalized

arg_parser = argparse.ArgumentParser(
    description="Generate a status line for swaybar",
    epilog="See `pydoc swaystatus` for full documentation.",
)
arg_parser.add_argument(
    "-V",
    "--version",
    action="version",
    version=__version__,
)
arg_parser.add_argument(
    "-c",
    "--config-file",
    metavar="FILE",
    type=path_normalized,
    help="specify configuration file",
)
arg_parser.add_argument(
    "-C",
    "--config-dir",
    metavar="DIRECTORY",
    type=path_normalized,
    help="specify configuration directory",
)
arg_parser.add_argument(
    "-D",
    "--data-dir",
    metavar="DIRECTORY",
    type=path_normalized,
    help="specify data directory",
)
arg_parser.add_argument(
    "-I",
    "--include",
    metavar="DIRECTORY",
    type=path_normalized,
    action="append",
    default=[],
    help="include an additional modules package",
)
arg_parser.add_argument(
    "-i",
    "--interval",
    metavar="SECONDS",
    type=float,
    help="specify update interval",
)
arg_parser.add_argument(
    "-e",
    "--click-events",
    action="store_true",
    default=None,
    help="enable click events",
)
arg_parser.add_argument(
    "-L",
    "--log-level",
    metavar="LEVEL",
    type=str.upper,
    choices=list(logging.getLevelNamesMapping().keys()),
    help="specify minimum logging level",
)
arg_parser.add_argument(
    "-v",
    "--verbose",
    dest="log_level",
    action="store_const",
    const="INFO",
    help="alias for --log-level=%(const)s",
)
arg_parser.add_argument(
    "-d",
    "--debug",
    dest="log_level",
    action="store_const",
    const="DEBUG",
    help="alias for --log-level=%(const)s",
)
