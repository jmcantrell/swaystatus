from typing import Self
from unittest import TestCase, main
from unittest.mock import patch

from swaystatus.daemon import Daemon
from swaystatus.status_line import StatusLine


class DaemonHarness:
    def __init__(self, test_case: TestCase, daemon: Daemon) -> None:
        self.test_case = test_case
        self.daemon = daemon

        patcher = patch.object(self.daemon._output_driver, "start")
        self.output_driver_start_mock = patcher.start()
        self.test_case.addCleanup(patcher.stop)

        patcher = patch.object(self.daemon._output_driver, "stop")
        self.output_driver_stop_mock = patcher.start()
        self.test_case.addCleanup(patcher.stop)

        if self.daemon._input_driver:
            patcher = patch.object(self.daemon._input_driver, "start")
            self.input_driver_start_mock = patcher.start()
            self.test_case.addCleanup(patcher.stop)

    def assert_input(self) -> None:
        self.input_driver_start_mock.assert_called()

    def assert_no_input(self) -> None:
        self.test_case.assertIsNone(self.daemon._input_driver, "expected input driver to not exist")

    def start(self) -> None:
        self.daemon.start()
        self.output_driver_start_mock.assert_called_once()

    def shutdown(self) -> None:
        self.daemon.stop()
        if self.daemon.is_alive():
            self.daemon.join(timeout=1.0)
            self.test_case.assertFalse(self.daemon.is_alive(), "daemon never died")
        self.output_driver_stop_mock.assert_called_once()

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.shutdown()


class TestDaemon(TestCase):
    def test_daemon_input(self) -> None:
        for click_events in [True, False]:
            with self.subTest(click_events=click_events):
                with DaemonHarness(self, Daemon(StatusLine([]), None, click_events)) as harness:
                    if click_events:
                        harness.assert_input()
                    else:
                        harness.assert_no_input()


if __name__ == "__main__":
    main()
