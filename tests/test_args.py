import argparse
from pathlib import Path
from typing import Any

from pytest import mark, raises

from swaystatus.args import arg_parser

arg_parser.exit_on_error = False


def parse(argv: list[str]) -> argparse.Namespace:
    return arg_parser.parse_args(argv)


def assert_arg(argv: list[str], attr: str, expected_value: Any) -> None:
    args = parse(argv)
    arg = getattr(args, attr)
    assert arg, f"expected argument to be parsed: {attr!r}"
    assert arg == expected_value, "argument value mismatch"


def assert_arg_invalid(argv: list[str]) -> None:
    with raises(argparse.ArgumentError) as exc_info:
        parse(argv)
    assert exc_info.match("invalid choice")


@mark.parametrize(
    ["attr", "option"],
    [
        (attr, option)
        for attr, options in [
            ("click_events", ["--click-events"]),
        ]
        for option in options
    ],
)
def test_bool(attr: str, option: str) -> None:
    """A boolean option is parsed."""
    assert_arg([option], attr, True)


@mark.parametrize(
    ["attr", "option"],
    [
        (attr, option)
        for attr, options in [
            ("interval", ["--interval", "-i"]),
        ]
        for option in options
    ],
)
def test_float(attr: str, option: str) -> None:
    """An early floating-point number option is overridden by a later one."""
    assert_arg([option, "1", option, "2"], attr, 2.0)


@mark.parametrize(
    ["attr", "option"],
    [
        (attr, option)
        for attr, options in [
            ("config_file", ["--config-file", "-c"]),
            ("config_dir", ["--config-dir", "-C"]),
            ("data_dir", ["--data-dir", "-D"]),
        ]
        for option in options
    ],
)
def test_path(attr: str, option: str) -> None:
    """An early path option is overridden by a later one."""
    assert_arg([option, "early", option, "late"], attr, Path("late"))


@mark.parametrize(
    ["attr", "option"],
    [
        (attr, option)
        for attr, options in [
            ("include", ["--include", "-I"]),
        ]
        for option in options
    ],
)
def test_paths(attr: str, option: str) -> None:
    """Certain options collect paths into a list."""
    argv = [option, "dir1", option, "dir2", option, "dir3"]
    expected_paths = list(map(Path, ["dir1", "dir2", "dir3"]))
    assert_arg(argv, attr, expected_paths)


def test_log_level() -> None:
    """An early log level is overridden by a later one."""
    option = "--log-level"
    assert_arg([option, "info", option, "error"], "log_level", "error")


@mark.parametrize("log_level", ["debug", "info", "warning", "error", "critical"])
def test_log_level_valid(log_level: str) -> None:
    """Valid log levels are allowed."""
    assert_arg(["--log-level", log_level], "log_level", log_level)


def test_log_level_invalid() -> None:
    """Invalid log levels are not allowed."""
    assert_arg_invalid(["--log-level", "bogus"])
