import random
from contextlib import contextmanager
from threading import Barrier, Event
from typing import Iterator, Self
from unittest import TestCase, main
from unittest.mock import DEFAULT, Mock, call, patch

from swaystatus.threading import Ticker


class TestTicker(TestCase):
    def setUp(self) -> None:
        self.harness = TickerHarness(self)
        self.addCleanup(self.harness.shutdown)

    def test_next_fires_tick(self) -> None:
        self.harness.ticker.start()
        expected_calls = random.randint(2, 10)
        self.harness.ticks(expected_calls)
        self.assertEqual(self.harness.tick_mock.call_count, expected_calls)

    def test_stop_before_waiting(self) -> None:
        self.harness.ticker.stop()
        self.harness.ticker.start()
        self.harness.tick_mock.assert_not_called()

    def test_stop_while_waiting(self) -> None:
        self.harness.ticker.start()
        with self.harness.next():
            self.harness.ticker.stop()
        self.harness.tick_mock.assert_not_called()


class TickerHarness:
    def __init__(self, test_case: TestCase) -> None:
        self.test_case = test_case

        self.tick_acquire = Barrier(2, timeout=1.0)
        self.tick_release = Event()

        def tick_side_effect(*args, **kwargs):
            self.tick_acquire.wait()
            self.tick_release.wait()
            return DEFAULT

        self.tick_mock = Mock(side_effect=tick_side_effect)
        self.ticker = Ticker(self.tick_mock, interval=5.0)

        self.next_acquire = Barrier(2, timeout=1.0)
        self.next_release = Event()

        def next_wait_side_effect(*args, **kwargs):
            self.next_acquire.wait()
            self.next_release.wait()
            return DEFAULT

        next_wait_patcher = patch.object(self.ticker._next, "wait", side_effect=next_wait_side_effect)
        self.next_wait_mock = next_wait_patcher.start()
        test_case.addCleanup(next_wait_patcher.stop)

        def next_set_side_effect(*args, **kwargs):
            self.next_release.set()
            return DEFAULT

        next_set_patcher = patch.object(self.ticker._next, "set", side_effect=next_set_side_effect)
        self.next_set_mock = next_set_patcher.start()
        test_case.addCleanup(next_set_patcher.stop)

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
        self.test_case.assertFalse(self.ticker.is_alive(), "thread never died")
        expected_calls = [call(timeout=self.ticker.interval)] * self.next_wait_mock.call_count
        self.test_case.assertEqual(self.next_wait_mock.mock_calls, expected_calls)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.shutdown()


if __name__ == "__main__":
    main()
