import json
import os
import random
from collections.abc import Iterator
from dataclasses import asdict
from io import StringIO
from signal import SIGCONT, SIGSTOP, Signals, getsignal, signal
from threading import Barrier
from unittest import TestCase, main
from unittest.mock import Mock, patch

from swaystatus.block import Block
from swaystatus.click_event import ClickEvent
from swaystatus.daemon import SIGNALS_SHUTDOWN, SIGNALS_UPDATE, Daemon
from swaystatus.element import BaseElement
from swaystatus.output import OutputDriver


class TestDaemon(TestCase):
    def setUp(self) -> None:
        signal_handlers_save = [(s, getsignal(s)) for s in (*SIGNALS_UPDATE, *SIGNALS_SHUTDOWN)]

        def restore_signal_handlers() -> None:
            for signum, handler in signal_handlers_save:
                signal(signum, handler)

        self.addCleanup(restore_signal_handlers)

    def test_signals(self) -> None:
        self.assertTrue(SIGNALS_UPDATE, "no update signals defined")
        self.assertTrue(SIGNALS_SHUTDOWN, "no shutdown signals defined")

        output_patcher = patch("swaystatus.daemon.OutputDriver")
        self.output_mock = output_patcher.start()
        self.addCleanup(output_patcher.stop)

        input_patcher = patch("swaystatus.daemon.InputDriver")
        self.input_mock = input_patcher.start()
        self.addCleanup(input_patcher.stop)

        shutdown_patcher = patch("swaystatus.daemon.Daemon.shutdown")
        shutdown_mock = shutdown_patcher.start()
        self.addCleanup(shutdown_patcher.stop)

        update_patcher = patch("swaystatus.daemon.Daemon.update")
        update_mock = update_patcher.start()
        self.addCleanup(update_patcher.stop)

        pid = os.getpid()
        signal_mocks = [
            (SIGNALS_UPDATE, update_mock),
            (SIGNALS_SHUTDOWN, shutdown_mock),
        ]

        Daemon([], None, False).start()

        for signums, mock in signal_mocks:
            for signum in signums:
                with self.subTest(signal=Signals(signum).name):
                    mock.reset_mock()
                    os.kill(pid, signum)
                    mock.assert_called_once()

    def test_io(self) -> None:
        tick_orig = OutputDriver.tick
        self.tick_called = Barrier(2, timeout=1.0)

        def tick_evented(*args, **kwargs):
            tick_orig(*args, **kwargs)
            self.tick_called.wait()

        tick_patcher = patch("swaystatus.daemon.OutputDriver.tick", tick_evented)
        tick_patcher.start()
        self.addCleanup(tick_patcher.stop)

        read_fd, write_fd = os.pipe()
        self.stdin_read = os.fdopen(read_fd, "r")
        self.stdin_write = os.fdopen(write_fd, "w")

        def cleanup_pipe() -> None:
            self.stdin_write.close()
            self.stdin_read.close()

        self.addCleanup(cleanup_pipe)

        class Element(BaseElement):
            def blocks(self) -> Iterator[Block]:
                yield self.block(self.name)

            def on_click_1(self, click_event: ClickEvent) -> bool:
                click_mock(self.name, click_event)
                return True

        click_mock = Mock()
        elements = [Element("a"), Element("b"), Element("c")]

        element = random.choice(elements)
        click_event = ClickEvent(
            name=element.name,
            instance=None,
            x=1900,
            y=10,
            button=1,
            event=274,
            relative_x=100,
            relative_y=8,
            width=120,
            height=18,
            scale=0.0,
        )

        stdout = StringIO()

        # start of input array
        self.stdin_write.write("[\n")
        self.stdin_write.flush()

        with patch("sys.stdout", stdout), patch("sys.stdin", self.stdin_read):
            daemon = Daemon(elements, None, True)
            daemon.start()
            self.addCleanup(daemon.shutdown)

            # initial output
            self.tick_called.wait()

            # update after click event handler returns true
            self.stdin_write.write(f",{json.dumps(asdict(click_event))}\n")
            self.stdin_write.flush()
            self.tick_called.wait()

            daemon.update()
            self.tick_called.wait()

            daemon.stop()
            daemon.join(timeout=1.0)

        stdout.seek(0)
        self.assertEqual(
            json.loads(stdout.readline().strip()),
            {
                "version": 1,
                "stop_signal": SIGSTOP,
                "cont_signal": SIGCONT,
                "click_events": True,
            },
        )
        self.assertEqual(stdout.readline(), "[[]\n")
        output_line = f",{json.dumps([{'full_text': e.name, 'name': e.name} for e in elements])}\n"
        self.assertEqual(stdout.readlines(), [output_line] * 3)
        click_mock.assert_called_once_with(element.name, click_event)


if __name__ == "__main__":
    main()
