from typing import Callable, Iterator
from unittest.mock import Mock

from pytest import fixture, mark
from pytest_mock import MockerFixture

from swaystatus.daemon import Daemon


class DaemonHarness:
    daemon: Daemon
    output_writer_start_mock: Mock
    output_writer_stop_mock: Mock
    input_reader_start_mock: Mock

    def __init__(self, mocker: MockerFixture, daemon: Daemon) -> None:
        self.daemon = daemon
        self.output_writer_start_mock = mocker.patch.object(self.daemon._output_writer, "start")
        self.output_writer_stop_mock = mocker.patch.object(self.daemon._output_writer, "stop")
        if self.daemon._input_reader:
            self.input_reader_start_mock = mocker.patch.object(self.daemon._input_reader, "start")

    def assert_input(self) -> None:
        self.input_reader_start_mock.assert_called()

    def assert_no_input(self) -> None:
        assert self.daemon._input_reader is None, "expected input reader to not exist"

    def start(self) -> None:
        self.daemon.start()
        self.output_writer_start_mock.assert_called_once()

    def shutdown(self) -> None:
        self.daemon.stop()
        self.daemon.join(timeout=1.0)
        assert not self.daemon.is_alive(), "daemon never died"
        self.output_writer_stop_mock.assert_called_once()


@fixture
def daemon_harnesser(mocker: MockerFixture) -> Iterator[Callable[[Daemon], DaemonHarness]]:
    harnesses = []

    def factory(daemon: Daemon) -> DaemonHarness:
        harness = DaemonHarness(mocker, daemon)
        harnesses.append(harness)
        harness.start()
        return harness

    yield factory

    for harness in harnesses:
        harness.shutdown()


@mark.parametrize("click_events", [None, False, True])
def test_daemon_input(click_events: bool, daemon_harnesser: Callable[[Daemon], DaemonHarness]) -> None:
    """Test that input activation is controlled by a keyword argument."""
    harness = daemon_harnesser(Daemon([], click_events=click_events))
    if click_events:
        harness.assert_input()
    else:
        harness.assert_no_input()
