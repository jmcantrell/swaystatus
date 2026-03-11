import itertools
import os
from multiprocessing import Process, Queue
from signal import SIGCONT, SIGINT, SIGTERM, SIGUSR1, Signals
from threading import Event
from typing import Self
from unittest import TestCase, main

from swaystatus.app import App
from swaystatus.daemon import Daemon
from swaystatus.status_line import StatusLine
from swaystatus.typing import Seconds


class FakeDaemon(Daemon):
    def __init__(self, queue: Queue[str]) -> None:
        super().__init__(StatusLine([]), None, False)
        self.queue = queue

    def update(self) -> None:
        self.queue.put("update")

    def start(self) -> None:
        self.queue.put("start")
        self._done = Event()
        self._done.wait()

    def stop(self) -> None:
        self.queue.put("stop")
        self._done.set()

    def join(self, timeout: Seconds = None) -> None:
        self._done.wait()

    def is_alive(self) -> bool:
        return not self._done.is_set()


def run_app(queue: Queue[str]) -> None:
    App(FakeDaemon(queue)).run()


class AppHarness:
    def __init__(self, test_case: TestCase) -> None:
        self.test_case = test_case
        self.queue: Queue[str] = Queue()
        self.process = Process(target=run_app, args=(self.queue,))

    def assert_message(self, value: str) -> None:
        self.test_case.assertEqual(self.queue.get(timeout=1.0), value, f"queue never put value: {value}")

    def signal(self, signum: int) -> None:
        assert self.process.pid
        os.kill(self.process.pid, signum)

    def start(self) -> None:
        self.process.start()
        self.test_case.assertTrue(self.process.pid)

    def shutdown(self) -> None:
        self.process.terminate()
        self.process.join(timeout=1.0)
        self.test_case.assertEqual(self.process.exitcode, 0, "process failed")

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.shutdown()


class TestApp(TestCase):
    def test_signals(self) -> None:
        for sig_update, sig_shutdown in itertools.product([SIGUSR1, SIGCONT], [SIGINT, SIGTERM]):
            with self.subTest(signals=[Signals(s).name for s in [sig_update, sig_shutdown]]):
                with AppHarness(self) as harness:
                    harness.assert_message("start")
                    harness.signal(sig_update)
                    harness.assert_message("update")
                    harness.signal(sig_shutdown)
                    harness.assert_message("stop")


if __name__ == "__main__":
    main()
