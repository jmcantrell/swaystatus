from dataclasses import fields
from pathlib import Path
from unittest import TestCase, main
from unittest.mock import mock_open, patch

from swaystatus.config import Config, Module, ModuleSettings

INVALID_TYPE = object()
EMPTY_STR = ""


class TestModuleSettings(TestCase):
    def test_field_env(self) -> None:
        env = {"TZ": "America/Chicago", "DISABLED": None}
        self.assertIs(ModuleSettings(env=env).env, env)

    def test_field_env_type(self) -> None:
        for env in [None, INVALID_TYPE]:
            with self.subTest(env=env), self.assertRaises(TypeError):
                ModuleSettings(env=env)  # type: ignore

    def test_field_env_key_type(self) -> None:
        for key in [None, INVALID_TYPE]:
            with self.subTest(key=key), self.assertRaises(TypeError):
                ModuleSettings(env={key: "value"})  # type: ignore

    def test_field_env_key_empty(self) -> None:
        with self.assertRaises(ValueError):
            ModuleSettings(env={EMPTY_STR: "America/Chicago"})

    def test_field_env_value_type(self) -> None:
        with self.assertRaises(TypeError):
            ModuleSettings(env={"key": INVALID_TYPE})  # type: ignore

    def test_field_on_click(self) -> None:
        on_click = {1: "true", 2: ["true"], 3: None}
        self.assertIs(ModuleSettings(on_click=on_click).on_click, on_click)

    def test_field_on_click_type(self) -> None:
        for on_click in [None, INVALID_TYPE]:
            with self.subTest(on_click=on_click), self.assertRaises(TypeError):
                ModuleSettings(on_click=on_click)  # type: ignore

    def test_field_on_click_key_type(self) -> None:
        for key in [None, INVALID_TYPE]:
            with self.subTest(key=key), self.assertRaises(TypeError):
                ModuleSettings(on_click={key: "true"})  # type: ignore

    def test_field_on_click_value_type(self) -> None:
        for value in [INVALID_TYPE, [INVALID_TYPE]]:
            with self.subTest(value=value), self.assertRaises(TypeError):
                ModuleSettings(on_click={1: value})  # type: ignore

    def test_field_on_click_value_empty(self) -> None:
        for value in [EMPTY_STR, [EMPTY_STR]]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                ModuleSettings(on_click={2: value})

    def test_field_params(self) -> None:
        params = {"text": "foo", "option": None}
        self.assertIs(ModuleSettings(params=params).params, params)

    def test_field_params_type(self) -> None:
        for params in [None, INVALID_TYPE]:
            with self.subTest(params=params), self.assertRaises(TypeError):
                ModuleSettings(params=params)  # type: ignore

    def test_field_params_key_type(self) -> None:
        for key in [None, INVALID_TYPE]:
            with self.subTest(key=key), self.assertRaises(TypeError):
                ModuleSettings(params={key: "value"})  # type: ignore

    def test_field_params_key_empty(self) -> None:
        with self.assertRaises(ValueError):
            ModuleSettings(params={EMPTY_STR: "whatever"})

    def test_parse_on_click_key_coerce(self) -> None:
        for key in ["1", b"1"]:
            with self.subTest(key=key):
                self.assertEqual(ModuleSettings.parse({"on_click": {key: "true"}}).on_click[1], "true")

    def test_parse_on_click_key_coerce_type(self) -> None:
        for key in [None, INVALID_TYPE]:
            with self.subTest(key=key), self.assertRaises(TypeError):
                ModuleSettings.parse({"on_click": {key: "false"}})

    def test_parse_on_click_key_coerce_value(self) -> None:
        for key in ["one", b"two"]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                ModuleSettings.parse({"on_click": {key: "false"}})


class TestModule(TestCase):
    def test_str(self) -> None:
        self.assertEqual(
            str(Module(name="foo")),
            "module name='foo' instance=None",
        )
        self.assertEqual(
            str(Module(name="foo", instance="a")),
            "module name='foo' instance='a'",
        )

    def test_field_name(self) -> None:
        self.assertIs(Module(name="clock").name, "clock")

    def test_field_name_type(self) -> None:
        for name in [None, INVALID_TYPE]:
            with self.subTest(name=name), self.assertRaises(TypeError):
                Module(name=name)  # type: ignore

    def test_field_name_empty(self) -> None:
        with self.assertRaises(ValueError):
            Module(name=EMPTY_STR)

    def test_field_instance(self) -> None:
        self.assertIsNone(Module(name="clock").instance)
        self.assertIsNone(Module(name="clock", instance=None).instance)
        self.assertIs(Module(name="clock", instance="home").instance, "home")

    def test_field_instance_type(self) -> None:
        with self.assertRaises(TypeError):
            Module(name="clock", instance=INVALID_TYPE)  # type: ignore

    def test_field_instance_empty(self) -> None:
        with self.assertRaises(ValueError):
            Module(name="clock", instance=EMPTY_STR)

    def test_field_settings(self) -> None:
        settings = ModuleSettings()
        self.assertIs(Module(name="clock", settings=settings).settings, settings)

    def test_field_settings_type(self) -> None:
        for settings in [None, INVALID_TYPE]:
            with self.subTest(settings=settings), self.assertRaises(TypeError):
                Module(name="clock", settings=settings)  # type: ignore

    def test_parse_settings_coerce(self) -> None:
        env = {"TZ": "America/Chicago"}
        on_click = {1: "true"}
        params = {"text": "foo"}
        self.assertEqual(
            Module.parse({"name": "clock", "settings": {"env": env, "on_click": on_click, "params": params}}),
            Module(name="clock", settings=ModuleSettings(env=env, on_click=on_click, params=params)),
        )


class TestConfig(TestCase):
    def test_fields(self) -> None:
        actual_fields = [f.name for f in fields(Config)]
        expected_fields = [
            "interval",
            "click_events",
            "env",
            "include",
            "settings",
            "modules",
        ]
        self.assertEqual(actual_fields, expected_fields)

    def test_init_default(self) -> None:
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
                self.assertIs(Config(interval=value).interval, value)

    def test_field_interval_type(self) -> None:
        with self.assertRaises(TypeError):
            Config(interval=INVALID_TYPE)  # type: ignore

    def test_field_interval_positive(self) -> None:
        for interval in [0.0, -1.0]:
            with self.subTest(interval=interval), self.assertRaises(ValueError):
                Config(interval=interval)

    def test_field_click_events(self) -> None:
        for value in [False, True]:
            with self.subTest(value=value):
                self.assertIs(Config(click_events=value).click_events, value)

    def test_field_click_events_type(self) -> None:
        for click_events in [None, INVALID_TYPE]:
            with self.subTest(click_events=click_events), self.assertRaises(TypeError):
                Config(click_events=click_events)  # type: ignore

    def test_field_env(self) -> None:
        env = {"TZ": "America/Chicago", "DISABLED": None}
        self.assertIs(Config(env=env).env, env)

    def test_field_env_type(self) -> None:
        for env in [None, INVALID_TYPE]:
            with self.subTest(env=env), self.assertRaises(TypeError):
                Config(env=env)  # type: ignore

    def test_field_env_key_type(self) -> None:
        for key in [None, INVALID_TYPE]:
            with self.subTest(key=key), self.assertRaises(TypeError):
                Config(env={key: "America/Chicago"})  # type: ignore

    def test_field_env_key_empty(self) -> None:
        with self.assertRaises(ValueError):
            Config(env={EMPTY_STR: "America/Chicago"})

    def test_field_env_value_type(self) -> None:
        with self.assertRaises(TypeError):
            Config(env={"TZ": INVALID_TYPE})  # type: ignore

    def test_field_include(self) -> None:
        include = [Path("/dir1"), Path("/dir2")]
        self.assertIs(Config(include=include).include, include)

    def test_field_include_type(self) -> None:
        for include in [None, INVALID_TYPE]:
            with self.subTest(include=include), self.assertRaises(TypeError):
                Config(include=include)  # type: ignore

    def test_field_include_item_type(self) -> None:
        for item in [None, INVALID_TYPE]:
            with self.subTest(item=item), self.assertRaises(TypeError):
                Config(include=[item])  # type: ignore

    def test_field_include_item_absolute_path(self) -> None:
        with self.assertRaises(ValueError):
            Config(include=[Path("relative")])

    def test_field_settings(self) -> None:
        settings = {"clock": ModuleSettings()}
        self.assertIs(Config(settings=settings).settings, settings)

    def test_field_settings_type(self) -> None:
        for settings in [None, INVALID_TYPE]:
            with self.subTest(settings=settings), self.assertRaises(TypeError):
                Config(settings=settings)  # type: ignore

    def test_field_settings_key_type(self) -> None:
        for key in [None, INVALID_TYPE]:
            with self.subTest(key=key), self.assertRaises(TypeError):
                Config(settings={key: ModuleSettings()})  # type: ignore

    def test_field_settings_key_empty(self) -> None:
        with self.assertRaises(ValueError):
            Config(settings={EMPTY_STR: ModuleSettings()})

    def test_field_settings_value_type(self) -> None:
        for value in [None, INVALID_TYPE]:
            with self.subTest(value=value), self.assertRaises(TypeError):
                Config(settings={"clock": value})  # type: ignore

    def test_field_modules(self) -> None:
        modules = [Module(name="clock")]
        self.assertIs(Config(modules=modules).modules, modules)

    def test_field_modules_type(self) -> None:
        for modules in [None, INVALID_TYPE]:
            with self.subTest(modules=modules), self.assertRaises(TypeError):
                Config(modules=modules)  # type: ignore

    def test_field_modules_item_type(self) -> None:
        for item in [None, INVALID_TYPE]:
            with self.subTest(item=item), self.assertRaises(TypeError):
                Config(modules=[item])  # type: ignore

    def test_modules_merged_order(self) -> None:
        modules = [
            Module(name="hostname"),
            Module(name="clock", instance="home"),
        ]
        config = Config(modules=modules)
        self.assertEqual(list(config.modules_merged()), modules)

    def test_modules_merged_env(self) -> None:
        config = Config(
            env={"LC_COLLATE": "C"},
            settings={"clock": ModuleSettings(env={"TZ": "UTC", "LC_TIME": "en_US"})},
            modules=[Module(name="clock", settings=ModuleSettings(env={"TZ": "America/Chicago"}))],
        )
        self.assertEqual(
            list(config.modules_merged()),
            [
                Module(
                    name="clock",
                    settings=ModuleSettings(env={"LC_COLLATE": "C", "LC_TIME": "en_US", "TZ": "America/Chicago"}),
                )
            ],
        )

    def test_modules_merged_on_click(self) -> None:
        config = Config(
            settings={"clock": ModuleSettings(on_click={1: "foot -H cal", 2: "date | wl-copy -n"})},
            modules=[Module(name="clock", settings=ModuleSettings(on_click={2: "foot -H timedatectl"}))],
        )
        self.assertEqual(
            list(config.modules_merged()),
            [Module(name="clock", settings=ModuleSettings(on_click={1: "foot -H cal", 2: "foot -H timedatectl"}))],
        )

    def test_modules_merged_params(self) -> None:
        config = Config(
            settings={"clock": ModuleSettings(params={"full_text": "%c", "short_text": "%r"})},
            modules=[Module(name="clock", settings=ModuleSettings(params={"short_text": "%s"}))],
        )
        self.assertEqual(
            list(config.modules_merged()),
            [Module(name="clock", settings=ModuleSettings(params={"full_text": "%c", "short_text": "%s"}))],
        )

    def test_parse_include_path_coerce(self) -> None:
        class PathThing:
            def __init__(self, path: str) -> None:
                self.path = path

            def __fspath__(self) -> str:
                return self.path

        config = Config.parse(
            {
                "include": [
                    "/path/to/dir1",
                    Path("/path/to/dir2"),
                    PathThing("/path/to/dir3"),
                ]
            }
        )
        self.assertEqual(
            config.include,
            [
                Path("/path/to/dir1"),
                Path("/path/to/dir2"),
                Path("/path/to/dir3"),
            ],
        )

    def test_parse_include_path_coerce_user(self) -> None:
        config = Config.parse({"include": ["~/path/to/dir"]})
        self.assertEqual(config.include, [Path.home() / "path/to/dir"])

    def test_parse_settings_coerce(self) -> None:
        env = {"TZ": "America/Chicago"}
        on_click = {1: "true"}
        params = {"text": "foo"}
        module_settings = ModuleSettings(env=env, on_click=on_click, params=params)
        self.assertEqual(
            Config.parse(
                {
                    "settings": {
                        "foo": {"env": env, "on_click": on_click, "params": params},
                        "bar": module_settings,
                    }
                }
            ),
            Config(settings={"foo": module_settings, "bar": module_settings}),
        )

    def test_parse_modules_coerce(self) -> None:
        module = Module(name="test", instance="a")
        self.assertEqual(
            Config.parse({"modules": [{"name": "test", "instance": "a"}, module]}),
            Config(modules=[module, module]),
        )

    def test_from_file(self) -> None:
        open_mock = mock_open(read_data=b"click_events = true")
        with patch("builtins.open", open_mock):
            self.assertEqual(Config.from_file("test.toml"), Config(click_events=True))
        open_mock.assert_called_once_with("test.toml", "rb")


if __name__ == "__main__":
    main()
