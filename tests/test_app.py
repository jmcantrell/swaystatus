import os
import random
from multiprocessing import Process, Queue
from signal import Signals
from threading import Event
from typing import Self
from unittest import TestCase, main
from unittest.mock import Mock

from swaystatus.app import SIGNALS_SHUTDOWN, SIGNALS_UPDATE, App
from swaystatus.daemon import Daemon
from swaystatus.status_line import StatusLine


class TestApp(TestCase):
    def setUp(self) -> None:
        self.daemon_mock = Mock()
        self.app = App(self.daemon_mock)

    def test_forwards_to_daemon(self) -> None:
        self.app.start()
        self.daemon_mock.start.assert_called_once()
        self.app.update()
        self.daemon_mock.update.assert_called_once()
        self.app.stop()
        self.daemon_mock.stop.assert_called_once()


class TestAppProcess(TestCase):
    def test_signal_update(self) -> None:
        for signum in SIGNALS_UPDATE:
            with self.subTest(signal=Signals(signum).name), AppProcessHarness(self) as harness:
                for _ in range(random.randint(5, 10)):
                    harness.signal(signum)
                    harness.assert_message("update")

    def test_signal_shutdown(self) -> None:
        for signum in SIGNALS_SHUTDOWN:
            with self.subTest(signal=Signals(signum).name), AppProcessHarness(self) as harness:
                harness.signal(signum)
                harness.assert_message("stop")
                harness.process.join(timeout=1.0)


class AppProcessHarness:
    def __init__(self, test_case: TestCase) -> None:
        self.test_case = test_case
        self.queue: Queue[str] = Queue()
        self.process = Process(target=start_app, args=(self.queue,))

    def assert_message(self, value: str) -> None:
        self.test_case.assertEqual(self.queue.get(timeout=1.0), value)

    def signal(self, signum: int) -> None:
        assert self.process.pid
        os.kill(self.process.pid, signum)

    def start(self) -> None:
        self.process.start()
        self.test_case.assertTrue(self.process.pid)
        self.assert_message("start")

    def shutdown(self) -> None:
        self.process.terminate()
        self.process.join(timeout=1.0)
        self.test_case.assertEqual(self.process.exitcode, 0)

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.shutdown()


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

    def join(self, timeout: float | int | None = None) -> None:
        self._done.wait()

    def is_alive(self) -> bool:
        return not self._done.is_set()


def start_app(queue: Queue[str]) -> None:
    App(FakeDaemon(queue)).start()


if __name__ == "__main__":
    main()
