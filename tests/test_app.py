import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from unittest.mock import Mock, call, patch

from swaystatus.app import App
from swaystatus.config import Config, EnvMapping, Module, ModuleSettings, OnClickMapping, ParamsMapping


class TestApp(TestCase):
    def setUp(self) -> None:
        argv_patcher = patch("sys.argv", ["swaystatus"])
        argv_patcher.start()
        self.addCleanup(argv_patcher.stop)

        env_patcher = patch.dict(os.environ, clear=True)
        self.env = env_patcher.start()
        self.addCleanup(env_patcher.stop)

        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.home_path_fake = Path(temp_dir.name)

        home_patcher = patch("swaystatus.app.Path.home", return_value=self.home_path_fake)
        self.home_mock = home_patcher.start()
        self.addCleanup(home_patcher.stop)

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
        self.registry_find_mock.return_value = self.element_mock = Mock()

        self.config = Config()
        config_from_file_patcher = patch("swaystatus.app.Config.from_file", return_value=self.config)
        self.config_from_file_mock = config_from_file_patcher.start()
        self.addCleanup(config_from_file_patcher.stop)

        self.app = App()

    def test_default_config_dir(self) -> None:
        self.assertEqual(self.app.default_config_dir, self.home_path_fake / ".config/swaystatus")

    def test_default_config_dir_xdg_override(self) -> None:
        config_home = Path("/path/to/config")
        self.env["XDG_CONFIG_HOME"] = str(config_home)
        self.assertEqual(self.app.default_config_dir, config_home / "swaystatus")

    def test_config_dir_default(self) -> None:
        self.assertEqual(self.app.config_dir, self.app.default_config_dir)

    def test_config_dir_env_over_default(self) -> None:
        config_dir = Path("/path/to/config/dir")
        self.env["SWAYSTATUS_CONFIG_DIR"] = str(config_dir)
        self.assertEqual(self.app.config_dir, config_dir)

    def test_config_dir_arg_over_env(self) -> None:
        config_dir = Path("/path/to/config/dir")
        self.app.args.config_dir = config_dir
        self.assertEqual(self.app.config_dir, config_dir)

    def test_config_file_default(self) -> None:
        self.assertEqual(self.app.config_file, self.app.default_config_dir / "config.toml")

    def test_config_file_env_over_default(self) -> None:
        config_file = Path("/path/to/config/file")
        self.env["SWAYSTATUS_CONFIG_FILE"] = str(config_file)
        self.assertEqual(self.app.config_file, config_file)

    def test_config_file_arg_over_env(self) -> None:
        config_file = Path("/path/to/config/file")
        self.app.args.config_file = config_file
        self.assertEqual(self.app.config_file, config_file)

    def test_config_from_file(self) -> None:
        config_file = Path("/path/to/config/file")
        self.app.config_file = config_file
        self.assertIs(self.app.config, self.config)
        self.config_from_file_mock.assert_called_once_with(config_file)

    def test_interval_default(self) -> None:
        self.assertIsNone(self.app.interval)

    def test_interval_default_is_config(self) -> None:
        self.app.config.interval = 1.0
        self.assertEqual(self.app.interval, 1.0)

    def test_interval_arg_over_config(self) -> None:
        self.app.args.interval = 1.0
        self.app.config.interval = 2.0
        self.assertEqual(self.app.interval, 1.0)

    def test_click_events_default(self) -> None:
        self.assertFalse(self.app.click_events)

    def test_click_events_default_is_config(self) -> None:
        self.app.config.click_events = True
        self.assertTrue(self.app.click_events)

    def test_click_events_arg_over_config(self) -> None:
        self.app.args.click_events = True

    def test_default_data_dir(self) -> None:
        self.assertEqual(self.app.default_data_dir, self.home_path_fake / ".local/share/swaystatus")

    def test_default_data_dir_xdg_override(self) -> None:
        data_home = Path("/path/to/data")
        self.env["XDG_DATA_HOME"] = str(data_home)
        self.assertEqual(self.app.default_data_dir, data_home / "swaystatus")

    def test_data_dir_default(self) -> None:
        self.assertEqual(self.app.data_dir, self.app.default_data_dir)

    def test_data_dir_env_over_default(self) -> None:
        data_dir = Path("/path/to/data/dir")
        self.env["SWAYSTATUS_DATA_DIR"] = str(data_dir)
        self.assertEqual(self.app.data_dir, data_dir)

    def test_data_dir_arg_over_env(self) -> None:
        data_dir = Path("/path/to/data/dir")
        self.app.args.data_dir = data_dir
        self.assertEqual(self.app.data_dir, data_dir)

    def test_include(self) -> None:
        self.app.args.include = args_include = [
            self.home_path_fake / "arg/path1",
            self.home_path_fake / "arg/path2",
        ]
        self.app.config.include = config_include = [
            self.home_path_fake / "config/path1",
            self.home_path_fake / "config/path2",
        ]
        package_include = [
            self.home_path_fake / "package/path1",
            self.home_path_fake / "package/path2",
        ]
        self.env["SWAYSTATUS_PACKAGE_PATH"] = ":".join(map(str, package_include))
        self.app.data_dir = data_dir = Path("/path/to/data/dir")
        self.assertEqual(
            self.app.include,
            args_include + config_include + package_include + [data_dir / "modules"],
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
        settings1 = ModuleSettings(env=env1, on_click=on_click1, params=params1)
        settings2 = ModuleSettings(env=env2, on_click=on_click2, params=params2)
        self.app.config.modules = modules = [
            Module(name="hostname", settings=settings1),
            Module(name="clock", instance="home", settings=settings2),
        ]

        self.assertEqual(self.app.elements, [self.element_mock.return_value] * len(modules))

        self.assertEqual(self.registry_find_mock.call_args_list, [call("hostname"), call("clock")])
        self.assertEqual(
            self.element_mock.call_args_list,
            [
                call("hostname", instance=None, env=env1, on_click=on_click1, **params1),
                call("clock", instance="home", env=env2, on_click=on_click2, **params2),
            ],
        )

    def test_daemon(self) -> None:
        self.assertIs(self.app.daemon, self.daemon_mock.return_value)
        self.daemon_mock.assert_called_once_with(self.app.elements, self.app.interval, self.app.click_events)

    def test_run_daemon(self) -> None:
        self.app.run()
        self.daemon_mock.return_value.start.assert_called_once()
        self.daemon_mock.return_value.join.assert_called_once()

    def test_run_log_level_default(self) -> None:
        self.app.run()
        self.log_level_mock.assert_not_called()

    def test_run_log_level_set(self) -> None:
        self.app.args.log_level = "DEBUG"
        self.app.run()
        self.log_level_mock.assert_called_once_with("DEBUG")


if __name__ == "__main__":
    main()
