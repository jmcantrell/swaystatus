import argparse
import logging
from pathlib import Path
from typing import Any
from unittest import TestCase, main

from swaystatus.args import Args, arg_parser

arg_parser.exit_on_error = False


class TestArgs(TestCase):
    def assert_arg(self, args: list[str], attr: str, expected_value: Any) -> None:
        arg = getattr(Args.parse(args), attr)
        self.assertEqual(arg, expected_value, "argument value mismatch")

    def assert_arg_invalid(self, args: list[str]) -> argparse.ArgumentError:
        with self.assertRaises(argparse.ArgumentError) as raised:
            Args.parse(args)
        return raised.exception

    def test_config_file(self) -> None:
        for option in ["--config-file", "-c"]:
            with self.subTest(option=option):
                self.assert_arg([option, "/file"], "config_file", Path("/file"))

    def test_config_dir(self) -> None:
        for option in ["--config-dir", "-C"]:
            with self.subTest(option=option):
                self.assert_arg([option, "/dir"], "config_dir", Path("/dir"))

    def test_data_dir(self) -> None:
        for option in ["--data-dir", "-D"]:
            with self.subTest(option=option):
                self.assert_arg([option, "/dir"], "data_dir", Path("/dir"))

    def test_include(self) -> None:
        for option in ["--include", "-I"]:
            with self.subTest(option=option):
                self.assert_arg([option, "/dir1", option, "/dir2"], "include", [Path("/dir1"), Path("/dir2")])

    def test_log_level(self) -> None:
        for option in ["--log-level", "-L"]:
            for level in logging.getLevelNamesMapping():
                with self.subTest(option=option, level=level):
                    self.assert_arg([option, level], "log_level", level)

    def test_log_level_invalid(self) -> None:
        for option in ["--log-level", "-L"]:
            with self.subTest(option=option):
                self.assert_arg_invalid([option, "bogus"])

    def test_verbose(self) -> None:
        for option in ["--verbose", "-v"]:
            with self.subTest(option=option):
                self.assert_arg([option], "log_level", "INFO")

    def test_debug(self) -> None:
        for option in ["--debug", "-d"]:
            with self.subTest(option=option):
                self.assert_arg([option], "log_level", "DEBUG")


if __name__ == "__main__":
    main()
