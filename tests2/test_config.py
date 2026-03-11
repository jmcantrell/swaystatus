from pathlib import Path
from unittest import TestCase, main

from swaystatus.config import Config


class TestConfig(TestCase):
    def test_module_keys(self) -> None:
        config = Config(
            modules=[
                {"name": "clock"},
                {"name": "clock", "instance": "home"},
            ]
        )
        self.assertEqual(
            list(config.module_keys()),
            [
                ("clock", None),
                ("clock", "home"),
            ],
        )

    def test_module_missing(self) -> None:
        with self.assertRaises(KeyError):
            Config().module("clock")
        with self.assertRaises(KeyError):
            Config().module("clock", "home")

    def test_module_empty(self) -> None:
        config = Config(
            modules=[
                {"name": "clock"},
                {"name": "clock", "instance": "home"},
            ]
        )
        self.assertEqual(config.module("clock"), {})
        self.assertEqual(config.module("clock", "home"), {})

    def test_module_env(self) -> None:
        config = Config(
            env={
                "LC_COLLATE": "C",
            },
            settings={
                "clock": {
                    "env": {
                        "TZ": "UTC",
                        "LC_TIME": "en_US",
                    },
                }
            },
            modules=[
                {
                    "name": "clock",
                    "env": {
                        "TZ": "America/Chicago",
                    },
                },
            ],
        )
        self.assertEqual(
            config.module("clock"),
            {
                "env": {
                    "LC_COLLATE": "C",
                    "LC_TIME": "en_US",
                    "TZ": "America/Chicago",
                }
            },
        )

    def test_module_on_click(self) -> None:
        config = Config(
            settings={
                "clock": {
                    "on_click": {
                        1: "foot -H cal",
                        2: "date | wl-copy -n",
                    },
                }
            },
            modules=[
                {
                    "name": "clock",
                    "on_click": {
                        2: "foot -H timedatectl",
                    },
                },
            ],
        )
        self.assertEqual(
            config.module("clock"),
            {
                "on_click": {
                    1: "foot -H cal",
                    2: "foot -H timedatectl",
                },
            },
        )

    def test_module_params(self) -> None:
        config = Config(
            settings={
                "clock": {
                    "params": {
                        "full_text": "%c",
                        "short_text": "%r",
                    },
                }
            },
            modules=[
                {
                    "name": "clock",
                    "params": {
                        "short_text": "%s",
                    },
                },
            ],
        )
        self.assertEqual(
            config.module("clock"),
            {
                "full_text": "%c",
                "short_text": "%s",
            },
        )

    def test_from_file(self) -> None:
        config_file = Path(__file__).parent / "data/config.toml"
        config = Config.from_file(config_file)
        self.assertEqual(config.interval, 5.0)
        self.assertTrue(config.click_events)
        self.assertEqual(
            config.module("clock"),
            {
                "full_text": "%r",
                "on_click": {1: "foot -H cal"},
                "env": {
                    "LC_COLLATE": "C",
                    "TZ": "America/Chicago",
                },
            },
        )


if __name__ == "__main__":
    main()
