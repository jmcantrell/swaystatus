import argparse
import logging
from pathlib import Path
from typing import Any
from unittest import TestCase, main

from swaystatus.args import arg_parser

arg_parser.exit_on_error = False


class TestArgs(TestCase):
    def test_click_events(self) -> None:
        for option in ["--click-events", "-e"]:
            with self.subTest(option=option):
                self.assert_arg([option], "click_events", True)

    def test_interval(self) -> None:
        for option in ["--interval", "-i"]:
            with self.subTest(option=option):
                self.assert_arg([option, "1", option, "2"], "interval", 2.0)

    def test_config_file(self) -> None:
        for option in ["--config-file", "-c"]:
            with self.subTest(option=option):
                self.assert_arg([option, "/early", option, "/late"], "config_file", Path("/late"))

    def test_config_file_paths_normalized(self) -> None:
        for value, normalized in [
            ("file", Path.cwd() / "file"),
            ("~/file", Path.home() / "file"),
            ("/dir1/../dir2", Path("/dir2")),
        ]:
            argv = ["--config-file", value]
            self.assert_arg(argv, "config_file", normalized)

    def test_config_dir(self) -> None:
        for option in ["--config-dir", "-C"]:
            with self.subTest(option=option):
                self.assert_arg([option, "/early", option, "/late"], "config_dir", Path("/late"))

    def test_config_dir_paths_normalized(self) -> None:
        for value, normalized in [
            ("dir", Path.cwd() / "dir"),
            ("~/dir", Path.home() / "dir"),
            ("/dir1/../dir2", Path("/dir2")),
        ]:
            argv = ["--config-dir", value]
            self.assert_arg(argv, "config_dir", normalized)

    def test_data_dir(self) -> None:
        for option in ["--data-dir", "-D"]:
            with self.subTest(option=option):
                self.assert_arg([option, "/early", option, "/late"], "data_dir", Path("/late"))

    def test_data_dir_paths_normalized(self) -> None:
        for value, normalized in [
            ("dir", Path.cwd() / "dir"),
            ("~/dir", Path.home() / "dir"),
            ("/dir1/../dir2", Path("/dir2")),
        ]:
            argv = ["--data-dir", value]
            self.assert_arg(argv, "data_dir", normalized)

    def test_include(self) -> None:
        for option in ["--include", "-I"]:
            with self.subTest(option=option):
                argv = [option, "/dir1", option, "/dir2", option, "/dir3"]
                expected_paths = [Path("/dir1"), Path("/dir2"), Path("/dir3")]
                self.assert_arg(argv, "include", expected_paths)

    def test_include_path_normalized(self) -> None:
        for value, normalized in [
            ("dir", Path.cwd() / "dir"),
            ("~/dir", Path.home() / "dir"),
            ("/dir1/../dir2", Path("/dir2")),
        ]:
            argv = ["--include", value]
            self.assert_arg(argv, "include", [normalized])

    def test_log_level(self) -> None:
        for option in ["--log-level", "-L"]:
            with self.subTest(option=option):
                self.assert_arg([option, "info", option, "error"], "log_level", "ERROR")

    def test_log_level_valid(self) -> None:
        for level in logging.getLevelNamesMapping():
            with self.subTest(level=level):
                self.assert_arg(["--log-level", level], "log_level", level)

    def test_log_level_invalid(self) -> None:
        self.assert_arg_invalid(["--log-level", "bogus"])

    def test_verbose(self) -> None:
        for option in ["--verbose", "-v"]:
            with self.subTest(option=option):
                self.assert_arg([option], "log_level", "INFO")

    def test_debug(self) -> None:
        for option in ["--debug", "-d"]:
            with self.subTest(option=option):
                self.assert_arg([option], "log_level", "DEBUG")

    def assert_arg(self, argv: list[str], attr: str, expected_value: Any) -> None:
        arg = getattr(arg_parser.parse_args(argv), attr)
        self.assertTrue(arg, f"expected argument to be parsed: {attr!r}")
        self.assertEqual(arg, expected_value, "argument value mismatch")

    def assert_arg_invalid(self, argv: list[str]) -> None:
        with self.assertRaisesRegex(argparse.ArgumentError, "invalid choice"):
            arg_parser.parse_args(argv)


if __name__ == "__main__":
    main()
