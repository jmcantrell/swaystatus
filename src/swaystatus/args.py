"""Command-line interface argument parsing."""

import argparse
import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Self

from . import __version__
from .logger import logger


@dataclass(slots=True, kw_only=True)
class Args:
    """Data class representing possible command-line arguments."""

    data_dir: Path | None = None
    config_dir: Path | None = None
    config_file: Path | None = None
    log_level: str | None = None
    include: list[Path] = field(default_factory=list)

    @classmethod
    def parse(cls, args: Sequence[str] | None = None) -> Self:
        return cls(**vars(arg_parser.parse_args(args)))


arg_parser = argparse.ArgumentParser(
    description="Generate a status line for swaybar",
    epilog="See `pydoc swaystatus` for full documentation.",
    formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=50),
    argument_default=argparse.SUPPRESS,  # to differentiate "not given" from explicitly unset
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
    type=Path,
    help="specify configuration file",
)
arg_parser.add_argument(
    "-C",
    "--config-dir",
    metavar="DIRECTORY",
    type=Path,
    help="specify configuration directory",
)
arg_parser.add_argument(
    "-D",
    "--data-dir",
    metavar="DIRECTORY",
    type=Path,
    help="specify data directory",
)
arg_parser.add_argument(
    "-I",
    "--include",
    metavar="DIRECTORY",
    type=Path,
    action="append",
    help="include an additional modules package",
)
arg_parser.add_argument(
    "-L",
    "--log-level",
    metavar="LEVEL",
    type=str.upper,
    choices=list(logging.getLevelNamesMapping().keys()),
    help=f"specify minimum logging level (default: {logging.getLevelName(logger.getEffectiveLevel())})",
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

__all__ = [Args.__name__]
