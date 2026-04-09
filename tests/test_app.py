import os
import random
from pathlib import Path
from string import ascii_letters
from unittest import TestCase, main
from unittest.mock import call, patch

from swaystatus.app import App
from swaystatus.config import Config, EnvMapping, Module, ModuleSettings, OnClickMapping, ParamsMapping
from swaystatus.element import BaseElement


class TestApp(TestCase):
    def setUp(self) -> None:
        argv_patcher = patch("sys.argv", ["swaystatus"])
        argv_patcher.start()
        self.addCleanup(argv_patcher.stop)

        env_patcher = patch.dict(os.environ, clear=True)
        self.env = env_patcher.start()
        self.addCleanup(env_patcher.stop)

        log_level_patcher = patch("swaystatus.app.logger.setLevel")
        self.log_level_mock = log_level_patcher.start()
        self.addCleanup(log_level_patcher.stop)

        daemon_patcher = patch("swaystatus.app.Daemon")
        self.daemon_mock = daemon_patcher.start()
        self.addCleanup(daemon_patcher.stop)

        registry_patcher = patch("swaystatus.app.Registry")
        self.registry_mock = registry_patcher.start()
        self.addCleanup(registry_patcher.stop)
        self.registry_find_mock = self.registry_mock.return_value.find
        self.element_mock = self.registry_find_mock.return_value

        self.config = Config()
        config_from_file_patcher = patch("swaystatus.app.Config.from_file", return_value=self.config)
        self.config_from_file_mock = config_from_file_patcher.start()
        self.addCleanup(config_from_file_patcher.stop)

        self.app = App()

    def test_config_home_default(self) -> None:
        self.assertEqual(self.app.config_home, Path.home() / ".config")

    def test_config_home_xdg_over_default(self) -> None:
        config_home = Path("/path/to/config")
        self.env["XDG_CONFIG_HOME"] = str(config_home)
        self.assertEqual(self.app.config_home, config_home)

    def test_config_dir_default_based_on_config_home(self) -> None:
        self.app.config_home = Path("/path/to/config")
        self.assertEqual(self.app.config_dir, self.app.config_home / "swaystatus")

    def test_config_dir_from_env_over_default(self) -> None:
        config_dir = Path("/path/to/config/dir")
        self.env["SWAYSTATUS_CONFIG_DIR"] = str(config_dir)
        self.assertEqual(self.app.config_dir, config_dir)

    def test_config_dir_from_arg_over_env(self) -> None:
        self.app.args.config_dir = Path("/path/to/config/dir")
        self.env["SWAYSTATUS_CONFIG_DIR"] = "/does/not/matter"
        self.assertEqual(self.app.config_dir, self.app.args.config_dir)

    def test_config_file_default_based_on_config_dir(self) -> None:
        self.app.config_dir = Path("/path/to/config/dir")
        self.assertEqual(self.app.config_file, self.app.config_dir / "config.toml")

    def test_config_file_from_env_over_default(self) -> None:
        config_file = Path("/path/to/config/file")
        self.env["SWAYSTATUS_CONFIG_FILE"] = str(config_file)
        self.assertEqual(self.app.config_file, config_file)

    def test_config_file_from_arg_over_env(self) -> None:
        self.app.args.config_file = Path("/path/to/config/file")
        self.env["SWAYSTATUS_CONFIG_FILE"] = "/does/not/matter"
        self.assertEqual(self.app.config_file, self.app.args.config_file)

    def test_config_from_file(self) -> None:
        self.app.config_file = Path("/path/to/config/file")
        self.assertIs(self.app.config, self.config)
        self.config_from_file_mock.assert_called_once_with(self.app.config_file)

    def test_data_home_default(self) -> None:
        self.assertEqual(self.app.data_home, Path.home() / ".local/share")

    def test_data_home_xdg_over_default(self) -> None:
        data_home = Path("/path/to/data")
        self.env["XDG_DATA_HOME"] = str(data_home)
        self.assertEqual(self.app.data_home, data_home)

    def test_data_dir_default_based_on_data_home(self) -> None:
        self.app.data_home = Path("/path/to/data")
        self.assertEqual(self.app.data_dir, self.app.data_home / "swaystatus")

    def test_data_dir_from_env_over_default(self) -> None:
        data_dir = Path("/path/to/data/dir")
        self.env["SWAYSTATUS_DATA_DIR"] = str(data_dir)
        self.assertEqual(self.app.data_dir, data_dir)

    def test_data_dir_from_arg_over_env(self) -> None:
        self.app.args.data_dir = Path("/path/to/data/dir")
        self.env["SWAYSTATUS_DATA_DIR"] = "/does/not/matter"
        self.assertEqual(self.app.data_dir, self.app.args.data_dir)

    def test_include(self) -> None:
        self.app.args.include = [Path.home() / "arg/path1", Path.home() / "arg/path2"]
        self.app.config.include = [Path.home() / "config/path1", Path.home() / "config/path2"]
        package_include = [Path.home() / "package/path1", Path.home() / "package/path2"]
        self.env["SWAYSTATUS_PACKAGE_PATH"] = ":".join(map(str, package_include))
        self.app.data_dir = data_dir = Path("/path/to/data/dir")
        self.assertEqual(
            self.app.include,
            self.app.args.include + self.app.config.include + package_include + [data_dir / "modules"],
        )

    def test_registry_from_include(self) -> None:
        self.app.include = [Path("/dir1"), Path("/dir2"), Path("/dir3")]
        self.assertIs(self.app.registry, self.registry_mock.return_value)
        self.registry_mock.assert_called_once_with(self.app.include)

    def test_elements(self) -> None:
        env1: EnvMapping = {"name": "first"}
        env2: EnvMapping = {"name": "second"}
        on_click1: OnClickMapping = {1: "true"}
        on_click2: OnClickMapping = {2: "true"}
        params1: ParamsMapping = {"text": "first"}
        params2: ParamsMapping = {"text": "second"}
        self.app.config.modules = [
            Module(
                name="hostname",
                settings=ModuleSettings(env=env1, on_click=on_click1, params=params1),
            ),
            Module(
                name="clock",
                instance="home",
                settings=ModuleSettings(env=env2, on_click=on_click2, params=params2),
            ),
        ]

        self.assertEqual(self.app.elements, [self.element_mock.return_value] * 2)

        self.assertEqual(
            self.registry_find_mock.call_args_list,
            [
                call("hostname"),
                call("clock"),
            ],
        )
        self.assertEqual(
            self.element_mock.call_args_list,
            [
                call("hostname", instance=None, env=env1, on_click=on_click1, **params1),
                call("clock", instance="home", env=env2, on_click=on_click2, **params2),
            ],
        )

    def test_daemon(self) -> None:
        self.app.elements = list(map(BaseElement, ascii_letters[: random.randint(2, 10)]))
        random.shuffle(self.app.elements)
        self.app.config.interval = random.randint(1, 5)
        self.app.config.click_events = random.choice([True, False])

        self.assertIs(self.app.daemon, self.daemon_mock.return_value)

        self.daemon_mock.assert_called_once_with(
            self.app.elements,
            self.app.config.interval,
            self.app.config.click_events,
        )

    def test_run_blocks_until_shutdown(self) -> None:
        self.app.run()
        self.daemon_mock.return_value.start.assert_called_once()
        self.daemon_mock.return_value.join.assert_called_once()

    def test_run_log_level_default(self) -> None:
        self.app.run()
        self.log_level_mock.assert_not_called()

    def test_run_log_level_from_arg_over_default(self) -> None:
        self.app.args.log_level = "DEBUG"
        self.app.run()
        self.log_level_mock.assert_called_once_with("DEBUG")


if __name__ == "__main__":
    main()
