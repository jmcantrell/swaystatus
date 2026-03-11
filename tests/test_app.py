import itertools
import os
from multiprocessing import Process, Queue
from queue import Empty
from signal import SIGCONT, SIGINT, SIGTERM, SIGUSR1
from threading import Event
from typing import Self

from pytest import fail, mark

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
    process: Process
    queue: Queue[str]

    def __init__(self) -> None:
        self.queue = Queue()
        self.process = Process(target=run_app, args=(self.queue,))

    def signal(self, signum: int) -> None:
        assert self.process.pid
        os.kill(self.process.pid, signum)

    def assert_message(self, value: str) -> None:
        try:
            assert self.queue.get(timeout=1.0) == value
        except Empty:
            fail(f"queue never put value: {value}")

    def start(self) -> None:
        self.process.start()
        assert self.process.pid

    def shutdown(self) -> None:
        self.process.terminate()
        self.process.join(timeout=1.0)
        assert self.process.exitcode == 0, "process failed"

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.shutdown()


@mark.parametrize(
    ["signal_update", "signal_shutdown"],
    itertools.product([SIGUSR1, SIGCONT], [SIGINT, SIGTERM]),
)
def test_app_signals(signal_update: int, signal_shutdown: int) -> None:
    """The app class responds to signals correctly."""
    with AppHarness() as harness:
        harness.assert_message("start")
        harness.signal(signal_update)
        harness.assert_message("update")
        harness.signal(signal_shutdown)
        harness.assert_message("stop")
