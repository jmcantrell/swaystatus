import itertools
import os
import signal
from contextlib import contextmanager
from threading import Thread
from typing import Iterator
from unittest import TestCase, main
from unittest.mock import Mock, patch

from swaystatus.app import SIGNALS_SHUTDOWN, SIGNALS_UPDATE, App


class TestApp(TestCase):
    def setUp(self) -> None:
        self.daemon_mock = Mock()
        self.app = App(self.daemon_mock)

    def test_forwards_start(self) -> None:
        self.app.start()
        self.daemon_mock.start.assert_called_once()

    def test_forwards_update(self) -> None:
        self.app.update()
        self.daemon_mock.update.assert_called_once()

    def test_forwards_stop(self) -> None:
        self.app.stop()
        self.daemon_mock.stop.assert_called_once()

    def test_forwards_join(self) -> None:
        self.app.join(timeout=4.0)
        self.daemon_mock.join.assert_called_once_with(timeout=4.0)

    def test_shutdown(self) -> None:
        self.app.shutdown()
        self.daemon_mock.stop.assert_called_once_with()
        self.daemon_mock.join.assert_called_once_with(timeout=5.0)

    def test_signal(self) -> None:
        shutdown_patcher = patch.object(self.app, "shutdown")
        shutdown_mock = shutdown_patcher.start()
        self.addCleanup(shutdown_patcher.stop)

        update_patcher = patch.object(self.app, "update")
        update_mock = update_patcher.start()
        self.addCleanup(update_patcher.stop)

        self.assertTrue(SIGNALS_UPDATE)
        self.assertTrue(SIGNALS_SHUTDOWN)

        pid = os.getpid()

        def signal_callback(signum: int) -> None:
            os.kill(pid, signum)

        signal_mocks = itertools.chain(
            zip(SIGNALS_UPDATE, update_mock),
            zip(SIGNALS_SHUTDOWN, shutdown_mock),
        )
        with signals_ignored(*SIGNALS_UPDATE, *SIGNALS_SHUTDOWN):
            self.app.start()
            for signum, mock in signal_mocks:
                thread = Thread(target=signal_callback, args=(signum,))
                thread.start()
                thread.join(timeout=1.0)
                mock.assert_called_once()


@contextmanager
def signals_ignored(*signums: int) -> Iterator:
    handlers_save = [(s, signal.getsignal(s)) for s in signums]
    try:
        yield
    finally:
        for signum, handler in handlers_save:
            signal.signal(signum, handler)


if __name__ == "__main__":
    main()
