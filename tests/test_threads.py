import random
from collections.abc import Iterator
from contextlib import contextmanager
from threading import Barrier, Event
from unittest import TestCase, main
from unittest.mock import DEFAULT, Mock, call, patch

from swaystatus.threads import Ticker


class TestTicker(TestCase):
    def setUp(self) -> None:
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
        self.addCleanup(next_wait_patcher.stop)

        def next_set_side_effect(*args, **kwargs):
            self.next_release.set()
            return DEFAULT

        next_set_patcher = patch.object(self.ticker._next, "set", side_effect=next_set_side_effect)
        self.next_set_mock = next_set_patcher.start()
        self.addCleanup(next_set_patcher.stop)

        def shutdown() -> None:
            self.ticker.stop()
            if self.ticker.is_alive():
                self.ticker.join(timeout=2.0)
            self.assertFalse(self.ticker.is_alive(), "thread never died")
            expected_calls = [call(timeout=self.ticker.interval)] * self.next_wait_mock.call_count
            self.assertEqual(self.next_wait_mock.mock_calls, expected_calls)

        self.addCleanup(shutdown)

    def test_next_fires_tick(self) -> None:
        self.ticker.start()
        expected_calls = random.randint(2, 10)
        self.ticks(expected_calls)
        self.assertEqual(self.tick_mock.call_count, expected_calls)

    def test_stop_before_waiting(self) -> None:
        self.ticker.stop()
        self.ticker.start()
        self.tick_mock.assert_not_called()

    def test_stop_while_waiting(self) -> None:
        self.ticker.start()
        with self.next():
            self.ticker.stop()
        self.tick_mock.assert_not_called()

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


if __name__ == "__main__":
    main()
