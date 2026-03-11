import argparse
import logging
from pathlib import Path
from typing import Any
from unittest import TestCase, main

from swaystatus.args import arg_parser

arg_parser.exit_on_error = False


class TestArgs(TestCase):
    def test_click_events(self) -> None:
        self.assert_arg(["--click-events"], "click_events", True)

    def test_interval(self) -> None:
        self.assert_arg(["--interval", "1", "--interval", "2"], "interval", 2.0)

    def test_config_file(self) -> None:
        for option in ["--config-file", "-c"]:
            with self.subTest(option=option):
                self.assert_arg([option, "early", option, "late"], "config_file", Path("late"))

    def test_config_dir(self) -> None:
        for option in ["--config-dir", "-C"]:
            with self.subTest(option=option):
                self.assert_arg([option, "early", option, "late"], "config_dir", Path("late"))

    def test_data_dir(self) -> None:
        for option in ["--data-dir", "-D"]:
            with self.subTest(option=option):
                self.assert_arg([option, "early", option, "late"], "data_dir", Path("late"))

    def test_include(self) -> None:
        for option in ["--include", "-I"]:
            with self.subTest(option=option):
                argv = [option, "dir1", option, "dir2", option, "dir3"]
                expected_paths = list(map(Path, ["dir1", "dir2", "dir3"]))
                self.assert_arg(argv, "include", expected_paths)

    def test_log_level(self) -> None:
        self.assert_arg(["--log-level", "info", "--log-level", "error"], "log_level", "ERROR")

    def test_log_level_valid(self) -> None:
        for level in logging.getLevelNamesMapping().keys():
            with self.subTest(level=level):
                self.assert_arg(["--log-level", level], "log_level", level)

    def test_log_level_invalid(self) -> None:
        self.assert_arg_invalid(["--log-level", "bogus"])

    def assert_arg(self, argv: list[str], attr: str, expected_value: Any) -> None:
        arg = getattr(arg_parser.parse_args(argv), attr)
        self.assertTrue(arg, f"expected argument to be parsed: {attr!r}")
        self.assertEqual(arg, expected_value, "argument value mismatch")

    def assert_arg_invalid(self, argv: list[str]) -> None:
        with self.assertRaisesRegex(argparse.ArgumentError, "invalid choice"):
            arg_parser.parse_args(argv)


if __name__ == "__main__":
    main()
