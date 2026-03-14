import json
import logging
import os
import random
import sys
from contextlib import contextmanager
from io import StringIO
from pathlib import Path
from signal import SIGCONT, SIGSTOP
from tempfile import TemporaryDirectory
from threading import Barrier
from typing import Iterator
from unittest import TestCase, main
from unittest.mock import Mock, call, patch

from swaystatus.args import arg_parser
from swaystatus.block import Block
from swaystatus.cli import build_elements, create_app, load_config, parse_args
from swaystatus.cli import main as cli_main
from swaystatus.click_event import ClickEvent
from swaystatus.config import Config
from swaystatus.element import BaseElement
from swaystatus.logging import logger
from swaystatus.output import OutputDriver


class TestParseArgs(TestCase):
    def setUp(self) -> None:
        argv_patcher = patch("sys.argv")
        argv_patcher.start()
        self.addCleanup(argv_patcher.stop)
        self.set_args()

        log_level_patcher = patch("swaystatus.logging.logger.setLevel")
        self.log_level_mock = log_level_patcher.start()
        self.addCleanup(log_level_patcher.stop)

    def set_args(self, *args: str) -> None:
        sys.argv = ["swaystatus", *args]

    def test_log_level_default(self) -> None:
        parse_args()
        self.log_level_mock.assert_called_once_with("WARNING")

    def test_log_level_set(self) -> None:
        self.set_args("--log-level=DEBUG")
        parse_args()
        self.log_level_mock.assert_called_once_with("DEBUG")


class TestLoadConfig(TestCase):
    def setUp(self) -> None:
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.home_path_fake = Path(temp_dir.name)

        home_patcher = patch("pathlib.Path.home", return_value=self.home_path_fake)
        self.home_mock = home_patcher.start()
        self.addCleanup(home_patcher.stop)

        config_from_file_patcher = patch("swaystatus.cli.Config.from_file")
        self.config_from_file_mock = config_from_file_patcher.start()
        self.addCleanup(config_from_file_patcher.stop)

        self.args = arg_parser.parse_args([])

    def touch_home_file(self, *components: str) -> Path:
        path = self.home_path_fake.joinpath(*components)
        path.parent.mkdir(parents=True)
        path.touch()
        return path

    def assert_loads_from_file(self, config_file: Path) -> None:
        expected = Config()
        self.config_from_file_mock.return_value = expected
        actual = load_config(self.args)
        self.config_from_file_mock.assert_called_once_with(config_file)
        self.assertIs(actual, expected)

    def test_default(self) -> None:
        config = load_config(self.args)
        self.config_from_file_mock.assert_not_called()
        self.assertEqual(config, Config())
        self.assert_loads_from_file(self.touch_home_file(".config/swaystatus/config.toml"))

    def test_file_arg(self) -> None:
        self.args.config_file = self.touch_home_file("some/other/config.toml")
        self.assert_loads_from_file(self.args.config_file)

    def test_file_self(self) -> None:
        config_file = self.touch_home_file("some/other/config.toml")
        env = {"SWAYSTATUS_CONFIG_FILE": str(config_file)}
        with patch.dict(os.environ, env, clear=True):
            self.assert_loads_from_file(config_file)

    def test_file_arg_over_self(self) -> None:
        self.args.config_file = self.touch_home_file("some/arg/config.toml")
        env_config_file = self.touch_home_file("some/env/config.toml")
        env = {"SWAYSTATUS_CONFIG_FILE": str(env_config_file)}
        with patch.dict(os.environ, env, clear=True):
            self.assert_loads_from_file(self.args.config_file)

    def test_dir_arg(self) -> None:
        config_file = self.touch_home_file("some/other/config.toml")
        self.args.config_dir = config_file.parent
        self.assert_loads_from_file(config_file)

    def test_dir_self(self) -> None:
        config_file = self.touch_home_file("some/other/config.toml")
        env = {"SWAYSTATUS_CONFIG_DIR": str(config_file.parent)}
        with patch.dict(os.environ, env, clear=True):
            self.assert_loads_from_file(config_file)

    def test_dir_xdg(self) -> None:
        config_file = self.touch_home_file("some/other/swaystatus/config.toml")
        env = {"XDG_CONFIG_HOME": str(config_file.parent.parent)}
        with patch.dict(os.environ, env, clear=True):
            self.assert_loads_from_file(config_file)

    def test_dir_arg_over_self(self) -> None:
        arg_config_file = self.touch_home_file("some/arg/config.toml")
        self.args.config_dir = arg_config_file.parent
        self_config_file = self.touch_home_file("some/self/config.toml")
        env = {"SWAYSTATUS_CONFIG_DIR": str(self_config_file.parent)}
        with patch.dict(os.environ, env, clear=True):
            self.assert_loads_from_file(arg_config_file)

    def test_dir_arg_over_xdg(self) -> None:
        arg_config_file = self.touch_home_file("some/arg/config.toml")
        self.args.config_dir = arg_config_file.parent
        xdg_config_file = self.touch_home_file("some/xdg/swaystatus/config.toml")
        env = {"XDG_CONFIG_HOME": str(xdg_config_file.parent.parent)}
        with patch.dict(os.environ, env, clear=True):
            self.assert_loads_from_file(arg_config_file)

    def test_dir_self_over_xdg(self) -> None:
        self_config_file = self.touch_home_file("some/self/config.toml")
        xdg_config_file = self.touch_home_file("some/xdg/swaystatus/config.toml")
        env = {
            "SWAYSTATUS_CONFIG_DIR": str(self_config_file.parent),
            "XDG_CONFIG_HOME": str(xdg_config_file.parent.parent),
        }
        with patch.dict(os.environ, env, clear=True):
            self.assert_loads_from_file(self_config_file)


class TestBuildElements(TestCase):
    def setUp(self) -> None:
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.home_path_fake = Path(temp_dir.name)

        home_patcher = patch("pathlib.Path.home", return_value=self.home_path_fake)
        self.home_mock = home_patcher.start()
        self.addCleanup(home_patcher.stop)

        self.default_home_modules_dir = self.home_path_fake / ".local/share/swaystatus/modules"

        self.args = arg_parser.parse_args([])

        package_registry_patcher = patch("swaystatus.cli.PackageRegistry", autospec=True)
        self.package_registry_mock = package_registry_patcher.start()
        self.addCleanup(package_registry_patcher.stop)

        instance = self.package_registry_mock.return_value  # autospec'd instance
        self.module_mock = instance.module
        self.module_mock.return_value = self.element_mock = Mock()

        config_patcher = patch("swaystatus.cli.Config", autospec=True)
        self.config_mock = config_patcher.start()
        self.addCleanup(config_patcher.stop)

    def test_include_default(self) -> None:
        self.assertEqual(list(build_elements(self.args, Config())), [])
        self.package_registry_mock.assert_called_once_with([self.default_home_modules_dir])
        self.module_mock.assert_not_called()
        self.element_mock.assert_not_called()

    def test_include(self) -> None:
        arg_include = [
            self.home_path_fake / "/arg/path1",
            self.home_path_fake / "/arg/path2",
        ]
        self.args.include = arg_include
        config_include: list[str | Path] = [
            self.home_path_fake / "/config/path1",
            self.home_path_fake / "/config/path2",
        ]
        config = Config(include=config_include)
        package_include = [
            self.home_path_fake / "/package/path1",
            self.home_path_fake / "/package/path2",
        ]
        env = {"SWAYSTATUS_PACKAGE_PATH": ":".join(map(str, package_include))}
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(list(build_elements(self.args, config)), [])
            self.package_registry_mock.assert_called_once_with(
                arg_include + config_include + package_include + [self.default_home_modules_dir]
            )
            self.module_mock.assert_not_called()
            self.element_mock.assert_not_called()

    def test_module_elements(self) -> None:
        expected_elements = [
            BaseElement("hostname"),
            BaseElement("clock", "home"),
        ]
        self.element_mock.side_effect = expected_elements
        config = Config(
            modules=[
                {"name": "hostname"},
                {"name": "clock", "instance": "home"},
            ]
        )
        actual_elements = list(build_elements(self.args, config))
        self.assertEqual(self.module_mock.call_args_list, [call("hostname"), call("clock")])
        self.assertEqual(self.element_mock.call_args_list, [call("hostname", None), call("clock", "home")])
        self.assertEqual(actual_elements, expected_elements)


class TestCreateApp(TestCase):
    def setUp(self) -> None:
        parse_args_patcher = patch("swaystatus.cli.parse_args")
        self.parse_args_mock = parse_args_patcher.start()
        self.addCleanup(parse_args_patcher.stop)

        load_config_patcher = patch("swaystatus.cli.load_config")
        self.load_config_mock = load_config_patcher.start()
        self.addCleanup(load_config_patcher.stop)

        build_elements_patcher = patch("swaystatus.cli.build_elements")
        self.build_elements_mock = build_elements_patcher.start()
        self.addCleanup(build_elements_patcher.stop)

        signals_patcher = patch("swaystatus.cli.App.register_signals")
        self.addCleanup(signals_patcher.stop)

        app_patcher = patch("swaystatus.cli.create_app")
        self.app_mock = app_patcher.start()
        self.addCleanup(app_patcher.stop)

        tick_orig = OutputDriver.tick
        self.tick_called = Barrier(2, timeout=1.0)

        def tick_evented(*args, **kwargs):
            tick_orig(*args, **kwargs)
            self.tick_called.wait()

        tick_patcher = patch.object(OutputDriver, "tick", tick_evented)
        self.tick_mock = tick_patcher.start()
        self.addCleanup(tick_patcher.stop)

        read_fd, write_fd = os.pipe()
        self.stdin_read = os.fdopen(read_fd, "r")
        self.stdin_write = os.fdopen(write_fd, "w")

        def cleanup_pipe() -> None:
            self.stdin_write.close()
            self.stdin_read.close()

        self.addCleanup(cleanup_pipe)

    def test_io(self) -> None:
        click_mock = Mock()

        class Element(BaseElement):
            def blocks(self) -> Iterator[Block]:
                yield self.block(self.name)

            def on_click_1(self, click_event: ClickEvent) -> bool:
                click_mock(self.name, click_event)
                return True

        args = arg_parser.parse_args([])
        self.parse_args_mock.return_value = args
        elements = list(map(Element, "abc"))
        config = Config(click_events=True, modules=[dict(name=e.name) for e in elements])
        self.load_config_mock.return_value = config
        self.build_elements_mock.return_value = iter(elements)

        element = random.choice(elements)
        click_event = ClickEvent(
            name=element.name,
            instance=None,
            x=1900,
            y=10,
            button=1,
            event=274,
            relative_x=100,
            relative_y=8,
            width=120,
            height=18,
            scale=0.0,
        )

        stdout = StringIO()
        self.stdin_write.write("[\n")
        self.stdin_write.flush()
        with patch("sys.stdout", stdout), patch("sys.stdin", self.stdin_read):
            app = create_app()
            app.start()
            self.addCleanup(app.shutdown)
            self.tick_called.wait()
            self.stdin_write.write(f"{json.dumps(click_event.as_dict())}\n")
            self.stdin_write.flush()
            self.tick_called.wait()
            app.stop()
            app.join(timeout=1.0)

        stdout.seek(0)
        self.assertEqual(
            json.loads(stdout.readline().strip()),
            dict(
                version=1,
                stop_signal=SIGSTOP,
                cont_signal=SIGCONT,
                click_events=True,
            ),
        )
        self.assertEqual(stdout.readline(), "[[]\n")
        output_line = f",{json.dumps([dict(full_text=e.name, name=e.name) for e in elements])}\n"
        self.assertEqual(stdout.readlines(), [output_line] * 2)
        click_mock.assert_called_once_with(element.name, click_event)


class TestMain(TestCase):
    def setUp(self) -> None:
        create_app_patcher = patch("swaystatus.cli.create_app")
        self.create_app_mock = create_app_patcher.start()
        self.addCleanup(create_app_patcher.stop)

        self.start_mock = Mock()
        app_mock = self.create_app_mock.return_value
        app_mock.start = self.start_mock

        self.fake_exc = Exception("BOOM!")

    def test_starts(self) -> None:
        self.assertEqual(cli_main(), 0)
        self.create_app_mock.assert_called_once()
        self.start_mock.assert_called_once()

    def test_create_raises(self) -> None:
        self.create_app_mock.side_effect = self.fake_exc
        with self.assert_raise_handled():
            self.assertEqual(cli_main(), 1)
        self.create_app_mock.assert_called()
        self.start_mock.assert_not_called()

    def test_start_raises(self) -> None:
        self.start_mock.side_effect = self.fake_exc
        with self.assert_raise_handled():
            self.assertEqual(cli_main(), 1)
        self.create_app_mock.assert_called()
        self.start_mock.assert_called()

    @contextmanager
    def assert_raise_handled(self) -> Iterator:
        with self.assertLogs(logger, logging.ERROR) as logged:
            yield

        record = logged.records[0]
        assert record.exc_info
        self.assertIs(record.exc_info[1], self.fake_exc)
        self.assertEqual(record.message, "unhandled exception in main")


if __name__ == "__main__":
    main()
