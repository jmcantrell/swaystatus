import random
from contextlib import contextmanager
from threading import Barrier, Event
from typing import Iterator, Self
from unittest.mock import Mock, call

from pytest import FixtureRequest, fixture
from pytest_mock import MockerFixture

from swaystatus.threading import Ticker


class TickerHarness:
    def __init__(self, mocker: MockerFixture, interval: float | None) -> None:
        self.tick_acquire = Barrier(2, timeout=1.0)
        self.tick_release = Event()

        def tick_side_effect(*args, **kwargs):
            self.tick_acquire.wait()
            self.tick_release.wait()
            return mocker.DEFAULT

        self.tick_mock = Mock(side_effect=tick_side_effect)
        self.ticker = Ticker(self.tick_mock, interval=interval)
        self.next_acquire = Barrier(2, timeout=1.0)
        self.next_release = Event()

        def next_wait_side_effect(*args, **kwargs):
            self.next_acquire.wait()
            self.next_release.wait()
            return mocker.DEFAULT

        self.next_wait_mock = mocker.patch.object(
            self.ticker._next,
            "wait",
            side_effect=next_wait_side_effect,
        )

        def next_set_side_effect(*args, **kwargs):
            self.next_release.set()
            return mocker.DEFAULT

        self.next_set_mock = mocker.patch.object(
            self.ticker._next,
            "set",
            side_effect=next_set_side_effect,
        )

    @contextmanager
    def next(self) -> Iterator:
        self.next_acquire.wait()
        yield
        self.next_release.set()

    @contextmanager
    def tick(self) -> Iterator:
        self.tick_acquire.wait()
        yield
        self.tick_release.set()

    def ticks(self, count: int) -> None:
        for stop in [False] * (count - 1) + [True]:
            with self.next():
                if stop:
                    self.ticker.stop()
            with self.tick():
                pass

    def shutdown(self) -> None:
        self.ticker.stop()
        if self.ticker.is_alive():
            self.ticker.join(timeout=2.0)
        assert not self.ticker.is_alive(), "thread never died"
        expected_calls = [call(timeout=self.ticker.interval)] * self.next_wait_mock.call_count
        assert self.next_wait_mock.mock_calls == expected_calls

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.shutdown()


class TestTicker:
    @fixture(autouse=True, params=[None, 5.0])
    def setup_harness(self, request: FixtureRequest, mocker: MockerFixture) -> Iterator:
        self.harness = TickerHarness(mocker, request.param)
        yield
        self.harness.shutdown()

    def test_next_fires_tick(self) -> None:
        """The tick callback is called on each tick."""
        self.harness.ticker.start()
        expected_calls = random.randint(2, 10)
        self.harness.ticks(expected_calls)
        assert self.harness.tick_mock.call_count == expected_calls

    def test_stop_before_waiting(self) -> None:
        """The ticker can be stopped before waiting for a tick."""
        self.harness.ticker.stop()
        self.harness.ticker.start()
        self.harness.tick_mock.assert_not_called()

    def test_stop_while_waiting(self) -> None:
        """The ticker can be stopped while waiting for a tick."""
        self.harness.ticker.start()
        with self.harness.next():
            self.harness.ticker.stop()
        self.harness.tick_mock.assert_not_called()
