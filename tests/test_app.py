import itertools
import os
from multiprocessing import Process, Queue
from queue import Empty
from threading import Event
from typing import Iterator

from pytest import fail, fixture, mark

from swaystatus.app import SIGNALS_SHUTDOWN, SIGNALS_UPDATE, App
from swaystatus.daemon import Daemon


class FakeDaemon(Daemon):
    def __init__(self, queue: Queue[str]) -> None:
        super().__init__([])
        self.queue = queue

    def start(self) -> None:
        self.queue.put("start")
        self._done = Event()
        self._done.wait()

    def stop(self) -> None:
        self.queue.put("stop")
        self._done.set()

    def update(self) -> None:
        self.queue.put("update")


def run_app(queue: Queue[str]) -> None:
    App(FakeDaemon(queue)).run()


class AppHarness:
    process: Process
    queue: Queue[str]

    def __init__(self) -> None:
        self.queue = Queue()
        self.process = Process(target=run_app, args=(self.queue,))

    def signal(self, signum: int) -> None:
        if self.process.pid:
            os.kill(self.process.pid, signum)

    def assert_message(self, value: str) -> None:
        try:
            assert self.queue.get(timeout=1) == value
        except Empty:
            fail(f"queue never put value: {value}")

    def start(self) -> None:
        self.process.start()
        assert self.process.pid

    def shutdown(self) -> None:
        self.process.kill()
        self.process.join(timeout=1.0)
        assert self.process.exitcode == 0, "process failed"


@fixture
def app_harness() -> Iterator[AppHarness]:
    app_harness = AppHarness()
    app_harness.start()
    yield app_harness
    app_harness.shutdown()


@mark.parametrize(
    ["signal_update", "signal_shutdown"],
    itertools.product(SIGNALS_UPDATE, SIGNALS_SHUTDOWN),
)
def test_app_signals(signal_update: int, signal_shutdown: int, app_harness) -> None:
    """Test that the app class responds to signals correctly."""
    app_harness.assert_message("start")
    app_harness.signal(signal_update)
    app_harness.assert_message("update")
    app_harness.signal(signal_shutdown)
    app_harness.assert_message("stop")
