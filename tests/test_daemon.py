import random
from threading import Barrier
from typing import Iterator, Self, Sequence
from unittest.mock import MagicMock, Mock

from pytest import mark
from pytest_mock import MockerFixture

from swaystatus.block import Block
from swaystatus.daemon import Daemon, InputDriver, OutputDriver
from swaystatus.status_line import StatusLine


class TestOutputDriver:
    def test_iterates_on_tick(self) -> None:
        """The output driver only iterates when the ticker ticks."""
        yield_acquire = Barrier(2, timeout=1.0)

        def fake_status_lines() -> Iterator[Sequence[Block]]:
            while True:
                yield_acquire.wait()
                yield []

        output_driver = OutputDriver(fake_status_lines(), None)
        output_driver.start()
        for _ in range(random.randint(2, 10)):
            output_driver.next()
            yield_acquire.wait()
        output_driver.stop()
        output_driver.join(timeout=1.0)


class TestInputDriver:
    def test_iterates_eagerly(self) -> None:
        """The input driver iterates as quickly as possible."""
        expected_calls = random.randint(2, 10)
        iter_mock = MagicMock()
        iter_mock.__iter__.return_value = iter([[]] * expected_calls)
        input_driver = InputDriver(iter_mock)
        input_driver.start()
        input_driver.join(timeout=1.0)
        assert list(iter_mock) == [], "expected iterator to be exhausted"


class DaemonHarness:
    daemon: Daemon
    output_driver_start_mock: Mock
    output_driver_stop_mock: Mock
    input_driver_start_mock: Mock

    def __init__(self, mocker: MockerFixture, daemon: Daemon) -> None:
        self.daemon = daemon
        self.output_driver_start_mock = mocker.patch.object(self.daemon._output_driver, "start")
        self.output_driver_stop_mock = mocker.patch.object(self.daemon._output_driver, "stop")
        if self.daemon._input_driver:
            self.input_driver_start_mock = mocker.patch.object(self.daemon._input_driver, "start")

    def assert_input(self) -> None:
        self.input_driver_start_mock.assert_called()

    def assert_no_input(self) -> None:
        assert self.daemon._input_driver is None, "expected input driver to not exist"

    def shutdown(self) -> None:
        self.daemon.stop()
        if self.daemon.is_alive():
            self.daemon.join(timeout=1.0)
            assert not self.daemon.is_alive(), "daemon never died"
        self.output_driver_stop_mock.assert_called_once()

    def __enter__(self) -> Self:
        self.daemon.start()
        self.output_driver_start_mock.assert_called_once()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.shutdown()


@mark.parametrize("click_events", [None, True, False])
def test_daemon_input(click_events: bool, mocker: MockerFixture) -> None:
    with DaemonHarness(mocker, Daemon(StatusLine([]), None, click_events)) as harness:
        if click_events:
            harness.assert_input()
        else:
            harness.assert_no_input()
