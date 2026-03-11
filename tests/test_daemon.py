from typing import Self
from unittest import TestCase, main
from unittest.mock import patch

from swaystatus.daemon import Daemon
from swaystatus.status_line import StatusLine


class TestDaemon(TestCase):
    def test_input(self) -> None:
        for click_events in [True, False]:
            with self.subTest(click_events=click_events):
                with DaemonHarness(self, Daemon(StatusLine([]), None, click_events)) as harness:
                    if click_events:
                        harness.input_start_mock.assert_called()
                    else:
                        self.assertIsNone(harness.daemon._input_driver)

    def test_update_on_start(self) -> None:
        with DaemonHarness(self, Daemon(StatusLine([]), None, False)) as harness:
            harness.output_next_mock.assert_called_once()

    def test_update_manual(self) -> None:
        with DaemonHarness(self, Daemon(StatusLine([]), None, False)) as harness:
            harness.output_next_mock.reset_mock()
            harness.daemon.update()
            harness.output_next_mock.assert_called_once()


class DaemonHarness:
    def __init__(self, test_case: TestCase, daemon: Daemon) -> None:
        self.test_case = test_case
        self.daemon = daemon

        output_start_patcher = patch.object(self.daemon._output_driver, "start")
        self.output_start_mock = output_start_patcher.start()
        self.test_case.addCleanup(output_start_patcher.stop)

        output_stop_patcher = patch.object(self.daemon._output_driver, "stop")
        self.output_stop_mock = output_stop_patcher.start()
        self.test_case.addCleanup(output_stop_patcher.stop)

        if self.daemon._input_driver:
            input_start_patcher = patch.object(self.daemon._input_driver, "start")
            self.input_start_mock = input_start_patcher.start()
            self.test_case.addCleanup(input_start_patcher.stop)

        output_next_patcher = patch.object(self.daemon._output_driver, "next")
        self.output_next_mock = output_next_patcher.start()
        self.test_case.addCleanup(output_next_patcher.stop)

    def start(self) -> None:
        self.daemon.start()
        self.output_start_mock.assert_called_once()

    def shutdown(self) -> None:
        self.daemon.stop()
        if self.daemon.is_alive():
            self.daemon.join(timeout=1.0)
            self.test_case.assertFalse(self.daemon.is_alive(), "daemon never died")
        self.output_stop_mock.assert_called_once()

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.shutdown()


if __name__ == "__main__":
    main()
