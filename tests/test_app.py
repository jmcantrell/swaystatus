import itertools
import os
from multiprocessing import Process, Queue
from threading import Event
from unittest import TestCase

from swaystatus.app import SIGNALS_SHUTDOWN, SIGNALS_UPDATE, App
from swaystatus.daemon import Daemon


class FakeDaemon(Daemon):
    def __init__(self, queue: Queue) -> None:
        super().__init__([], 0.0, False)
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


def run_app(queue: Queue) -> None:
    App(FakeDaemon(queue)).run()


class TestApp(TestCase):
    def test_signals(self) -> None:
        """Test that the app class responds to signals correctly."""
        for signal_update, signal_shutdown in itertools.product(SIGNALS_UPDATE, SIGNALS_SHUTDOWN):
            with self.subTest(signal_update=signal_update, signal_shutdown=signal_shutdown):
                queue: Queue[str] = Queue()
                process = Process(target=run_app, args=(queue,))
                process.start()
                self.assertEqual(queue.get(), "start")
                assert process.pid
                os.kill(process.pid, signal_update)
                self.assertEqual(queue.get(), "update")
                os.kill(process.pid, signal_shutdown)
                self.assertEqual(queue.get(), "stop")
                process.join(timeout=5)
                self.assertEqual(process.exitcode, 0)
