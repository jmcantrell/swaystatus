import itertools
import os
from multiprocessing import Process, Queue
from threading import Event

import pytest

from swaystatus.app import SIGNALS_SHUTDOWN, SIGNALS_UPDATE, App
from swaystatus.daemon import Daemon


class FakeDaemon(Daemon):
    def __init__(self, queue: Queue) -> None:
        super().__init__([], 0.0, False)
        self.queue = queue

    def start(self) -> None:
        self.queue.put("start")
        self._finish = Event()
        self._finish.wait()

    def stop(self) -> None:
        self.queue.put("stop")
        self._finish.set()

    def update(self) -> None:
        self.queue.put("update")


def run_app(queue: Queue) -> None:
    App(FakeDaemon(queue)).run()


@pytest.mark.parametrize(
    [
        "signal_shutdown",
        "signal_update",
    ],
    itertools.product(
        SIGNALS_SHUTDOWN,
        SIGNALS_UPDATE,
    ),
)
def test_app_signals(signal_shutdown: int, signal_update: int) -> None:
    """Ensure that the app class responds to signals correctly."""
    queue: Queue[str] = Queue()
    process = Process(target=run_app, args=(queue,))
    process.start()
    assert queue.get() == "start"
    assert process.pid
    os.kill(process.pid, signal_update)
    assert queue.get() == "update"
    os.kill(process.pid, signal_shutdown)
    assert queue.get() == "stop"
    process.join(timeout=5)
    assert process.exitcode == 0
