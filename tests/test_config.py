from dataclasses import fields
from pathlib import Path
from unittest import TestCase, main

from swaystatus.config import Config, EnvDict, ModuleDict, SettingsDict

INVALID_TYPE = object()
EMPTY_STR = ""


class TestConfig(TestCase):
    def test_fields(self) -> None:
        actual_field_names = [f.name for f in fields(Config)]
        expected_field_names = ["interval", "click_events", "env", "include", "settings", "modules"]
        self.assertEqual(actual_field_names, expected_field_names)

    def test_default(self) -> None:
        config = Config()
        self.assertIsNone(config.interval)
        self.assertIs(config.click_events, False)
        self.assertEqual(config.env, {})
        self.assertEqual(config.include, [])
        self.assertEqual(config.settings, {})
        self.assertEqual(config.modules, [])

    def test_field_interval(self) -> None:
        for value in [None, 1, 1.0]:
            with self.subTest(value=value):
                self.assertEqual(Config(interval=value).interval, value)

    def test_field_interval_type(self) -> None:
        with self.assertRaises(TypeError):
            Config(interval=INVALID_TYPE)  # type:ignore

    def test_field_interval_positive(self) -> None:
        with self.assertRaises(ValueError):
            Config(interval=0.0)
        with self.assertRaises(ValueError):
            Config(interval=-1.0)

    def test_field_click_events(self) -> None:
        for value in [False, True]:
            with self.subTest(value=value):
                self.assertEqual(Config(click_events=value).click_events, value)

    def test_field_click_events_type(self) -> None:
        with self.assertRaises(TypeError):
            Config(click_events=INVALID_TYPE)  # type:ignore

    def test_field_env(self) -> None:
        env: EnvDict = {"TZ": "America/Chicago"}
        self.assertEqual(Config(env=env).env, env)

    def test_field_env_type(self) -> None:
        with self.assertRaises(TypeError):
            Config(env=INVALID_TYPE)  # type:ignore

    def test_field_env_key_type(self) -> None:
        with self.assertRaises(TypeError):
            Config(env={INVALID_TYPE: "value"})  # type:ignore

    def test_field_env_value_type(self) -> None:
        with self.assertRaises(TypeError):
            Config(env={"key": INVALID_TYPE})  # type:ignore

    def test_field_include(self) -> None:
        self.assertEqual(Config(include=["path"]).include, [Path("path")])

    def test_field_include_type(self) -> None:
        with self.assertRaises(TypeError):
            Config(include=INVALID_TYPE)  # type:ignore

    def test_field_include_item_type(self) -> None:
        with self.assertRaises(TypeError):
            Config(include=[INVALID_TYPE])  # type:ignore

    def test_field_settings(self) -> None:
        settings: dict[str, SettingsDict] = {
            "clock": {
                "env": {"TZ": "America/Chicago"},
                "on_click": {1: "foot -H cal"},
                "params": {"foo": "test"},
            }
        }
        self.assertEqual(Config(settings=settings).settings, settings)

    def test_field_settings_type(self) -> None:
        with self.assertRaises(TypeError):
            Config(settings=INVALID_TYPE)  # type:ignore

    def test_field_settings_key_type(self) -> None:
        with self.assertRaises(TypeError):
            Config(settings={INVALID_TYPE: {}})  # type:ignore

    def test_field_settings_key_empty(self) -> None:
        with self.assertRaises(ValueError):
            Config(settings={EMPTY_STR: {}})

    def test_field_settings_value_type(self) -> None:
        with self.assertRaises(TypeError):
            Config(settings={"clock": INVALID_TYPE})  # type:ignore

    def test_field_settings_env_type(self) -> None:
        with self.assertRaises(TypeError):
            Config(settings={"clock": {"env": INVALID_TYPE}})  # type:ignore

    def test_field_settings_env_key_type(self) -> None:
        with self.assertRaises(TypeError):
            Config(settings={"clock": {"env": {INVALID_TYPE: "America/Chicago"}}})  # type: ignore

    def test_field_settings_env_key_empty(self) -> None:
        with self.assertRaises(ValueError):
            Config(settings={"clock": {"env": {EMPTY_STR: "America/Chicago"}}})

    def test_field_settings_env_value_type(self) -> None:
        with self.assertRaises(TypeError):
            Config(settings={"clock": {"env": {"TZ": INVALID_TYPE}}})  # type: ignore

    def test_field_settings_on_click_type(self) -> None:
        with self.assertRaises(TypeError):
            Config(settings={"clock": {"on_click": INVALID_TYPE}})  # type: ignore

    def test_field_settings_on_click_key_type(self) -> None:
        with self.assertRaises(TypeError):
            Config(settings={"clock": {"on_click": {INVALID_TYPE: "foot -H timedatectl"}}})  # type: ignore

    def test_field_settings_on_click_value_type(self) -> None:
        with self.assertRaises(TypeError):
            Config(settings={"clock": {"on_click": {2: INVALID_TYPE}}})  # type: ignore

    def test_field_settings_on_click_value_item_type(self) -> None:
        with self.assertRaises(TypeError):
            Config(settings={"clock": {"on_click": {2: [INVALID_TYPE]}}})  # type: ignore

    def test_field_settings_params_type(self) -> None:
        with self.assertRaises(TypeError):
            Config(settings={"clock": {"params": INVALID_TYPE}})  # type:ignore

    def test_field_settings_params_key_type(self) -> None:
        with self.assertRaises(TypeError):
            Config(settings={"clock": {"params": {INVALID_TYPE: "whatever"}}})  # type:ignore

    def test_field_modules_type(self) -> None:
        with self.assertRaises(TypeError):
            Config(modules=INVALID_TYPE)  # type:ignore

    def test_field_modules_item_type(self) -> None:
        with self.assertRaises(TypeError):
            Config(modules=[INVALID_TYPE])  # type:ignore

    def test_field_modules_item_name_required(self) -> None:
        with self.assertRaises(ValueError):
            Config(modules=[{}])  # type:ignore

    def test_field_modules_item_name_type(self) -> None:
        with self.assertRaises(TypeError):
            Config(modules=[{"name": INVALID_TYPE}])  # type:ignore

    def test_field_modules_item_name_empty(self) -> None:
        with self.assertRaises(ValueError):
            Config(modules=[{"name": EMPTY_STR}])

    def test_field_modules_item_instance(self) -> None:
        modules: list[ModuleDict] = [{"name": "clock", "instance": "home"}]
        self.assertEqual(Config(modules=modules).modules, modules)

    def test_field_modules_item_instance_missing(self) -> None:
        modules: list[ModuleDict] = [{"name": "clock"}]
        self.assertEqual(Config(modules=modules).modules, modules)

    def test_field_modules_item_instance_type(self) -> None:
        with self.assertRaises(TypeError):
            Config(modules=[{"name": "clock", "instance": INVALID_TYPE}])  # type:ignore

    def test_field_modules_item_instance_empty(self) -> None:
        with self.assertRaises(ValueError):
            Config(modules=[{"name": "clock", "instance": EMPTY_STR}])

    def test_field_modules_item_env_type(self) -> None:
        with self.assertRaises(TypeError):
            Config(modules=[{"name": "clock", "env": INVALID_TYPE}])  # type:ignore

    def test_field_modules_item_env_key_type(self) -> None:
        with self.assertRaises(TypeError):
            Config(modules=[{"name": "clock", "env": {INVALID_TYPE: "America/Chicago"}}])  # type: ignore

    def test_field_modules_item_env_key_empty(self) -> None:
        with self.assertRaises(ValueError):
            Config(modules=[{"name": "clock", "env": {EMPTY_STR: "America/Chicago"}}])

    def test_field_modules_item_env_value_type(self) -> None:
        with self.assertRaises(TypeError):
            Config(settings={"clock": {"env": {"key": INVALID_TYPE}}})  # type:ignore

    def test_field_modules_on_click_type(self) -> None:
        with self.assertRaises(TypeError):
            Config(modules=[{"name": "clock", "on_click": INVALID_TYPE}])  # type: ignore

    def test_field_modules_on_click_key_type(self) -> None:
        with self.assertRaises(TypeError):
            Config(modules=[{"name": "clock", "on_click": {INVALID_TYPE: "foot -H timedatectl"}}])  # type: ignore

    def test_field_modules_on_click_value_type(self) -> None:
        with self.assertRaises(TypeError):
            Config(modules=[{"name": "clock", "on_click": {2: INVALID_TYPE}}])  # type: ignore

    def test_field_modules_on_click_value_item_type(self) -> None:
        with self.assertRaises(TypeError):
            Config(modules=[{"name": "clock", "on_click": {2: [INVALID_TYPE]}}])  # type: ignore

    def test_field_modules_params_type(self) -> None:
        with self.assertRaises(TypeError):
            Config(modules=[{"name": "clock", "params": INVALID_TYPE}])  # type:ignore

    def test_field_modules_params_key_type(self) -> None:
        with self.assertRaises(TypeError):
            Config(modules=[{"name": "clock", "params": {INVALID_TYPE: "whatever"}}])  # type: ignore

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
        config_file = Path(__file__).parent / "data/configs/all.toml"
        config = Config.from_file(config_file)
        self.assertEqual(config.interval, 5.0)
        self.assertTrue(config.click_events)
        self.assertEqual(
            config.include,
            [
                Path.home() / "expand/user",
                Path("/path/to/modules"),
            ],
        )
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
        self.assertEqual(
            config.module("clock", "home"),
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
