import json
from io import StringIO
from random import randint
from threading import Event
from typing import Iterator
from unittest import TestCase, main
from unittest.mock import DEFAULT, Mock, patch

from swaystatus.block import Block
from swaystatus.element import BaseElement
from swaystatus.threading import InputReader, OutputWriter, Ticker, UpdateRunner


class TestTicker(TestCase):
    def test_stop(self) -> None:
        """Test that a ticker can be stopped."""
        ticker = Ticker()
        with patch.object(ticker._stopper, "is_set", return_value=True):
            ticker.start(lambda: None)
            assert ticker._thread
            self.addCleanup(ticker._thread.join)
            with patch.object(ticker._thread, "join", autospec=True, wraps=ticker._thread.join) as join_mock:
                ticker.stop()
                join_mock.assert_called_once()

    def test_tick(self) -> None:
        """Test that a ticker can be advanced manually."""
        tick = Event()

        def on_tick() -> None:
            tick.set()

        ticker = Ticker()
        ticker.start(on_tick)
        self.addCleanup(ticker.stop)
        if not tick.wait(timeout=1.0):
            self.fail("initial tick never happened")
        tick.clear()
        ticker.tick()
        if not tick.wait(timeout=1.0):
            self.fail("manual tick never happened")
        ticker.stop()

    def test_interval(self) -> None:
        """Test that a ticker will wait for the given interval before the next tick."""
        wait_called = Event()

        def wait_side_effect(*args, **kwargs):
            wait_called.set()
            return DEFAULT

        for interval in [None, 5.0]:
            with self.subTest(interval=interval):
                wait_called.clear()
                ticker = Ticker(interval=interval)
                with patch.object(ticker._waiter, "wait", autospec=True, wraps=ticker._waiter.wait) as wait_mock:
                    wait_mock.side_effect = wait_side_effect
                    ticker.start(lambda: None)
                    self.addCleanup(ticker.stop)
                    if not wait_called.wait(timeout=1.0):
                        self.fail("wait was never called")
                    ticker.stop()
                    wait_mock.assert_called_once_with(timeout=interval)

    def test_first_tick_immediate(self) -> None:
        """Test that a ticker will tick immediately on start."""

        first_tick = Event()
        wait_called = Event()

        def on_tick() -> None:
            first_tick.set()

        ticker = Ticker()

        def wait_side_effect(*args, **kwargs):
            wait_called.set()
            return DEFAULT

        with patch.object(ticker._waiter, "wait", autospec=True, wraps=ticker._waiter.wait) as wait_mock:
            wait_mock.side_effect = wait_side_effect
            ticker.start(on_tick)
            if not first_tick.wait(timeout=1.0):
                self.fail("first tick never happened")
            ticker.stop()
            if not wait_called.wait(timeout=1.0):
                self.fail("wait was never called")
            wait_mock.assert_called_once()


class TestOutputWriter(TestCase):
    def test_output(self) -> None:
        """Test that the output processor steadily writes status lines to the target file."""

        class Element(BaseElement):
            name = "test"

            def blocks(self) -> Iterator[Block]:
                yield self.block("foo")

        output_file = StringIO()
        output_writer = OutputWriter(output_file, [Element()])
        num_lines = randint(5, 10)
        process_yielded = Event()
        process_orig = output_writer._output_processor.process

        def process_side_effect(*args, **kwargs):
            for status_line in process_orig(*args, **kwargs):
                process_yielded.set()
                yield status_line
                process_yielded.clear()

        with patch.object(
            output_writer._output_processor,
            "process",
            autospec=True,
            wraps=output_writer._output_processor.process,
        ) as process_mock:
            process_mock.side_effect = process_side_effect
            output_writer.start()
            self.addCleanup(output_writer.stop)
            i = 0
            while True:
                if not process_yielded.wait(timeout=1.0):
                    self.fail(f"process never yielded item number {i + 1}")
                i += 1
                if i == num_lines:
                    break
                process_yielded.clear()
                output_writer.update()

        output_file.seek(0)
        self.assertIsInstance(json.loads(output_file.readline().strip()), dict)  # header
        self.assertEqual(output_file.readline(), "[[]\n")  # body start
        self.assertEqual(len(output_file.readlines()), num_lines)  # status lines


class TestInputReader(TestCase):
    def setUp(self) -> None:
        self.output_file = StringIO()
        self.output_writer = OutputWriter(self.output_file, [])
        self.input_file = StringIO()
        self.input_reader = InputReader(self.input_file, [], self.output_writer)
        self.process_mock = self.enterContext(patch("swaystatus.input.InputProcessor.process", autospec=True))
        self.update_handler_mock = Mock()
        self.update_handler_called = Event()
        self.update_mock = self.enterContext(patch("swaystatus.threading.OutputWriter.update", autospec=True))
        self.update_called = Event()

        def handler_side_effect(*args, **kwargs):
            self.update_handler_called.set()
            return DEFAULT

        self.update_handler_mock.side_effect = handler_side_effect

        def update_side_effect(*args, **kwargs):
            self.update_called.set()

        self.update_mock.side_effect = update_side_effect

    def test_update_false(self) -> None:
        """Test that no update is run if not requested."""
        self.process_mock.return_value = [False]
        self.input_reader.start()
        assert self.input_reader._thread
        self.input_reader._thread.join()
        self.update_mock.assert_not_called()

    def test_update_true(self) -> None:
        """Test that an update is run if requested."""
        self.process_mock.return_value = [True]
        self.input_reader.start()
        if not self.update_called.wait(timeout=1.0):
            self.fail("update never called")
        assert self.input_reader._thread
        self.input_reader._thread.join()

    def test_update_handler_false(self) -> None:
        """Test that an update is not run if the handler fails."""
        self.update_handler_mock.return_value = False
        self.process_mock.return_value = [self.update_handler_mock]
        self.input_reader.start()
        if not self.update_handler_called.wait(timeout=1.0):
            self.fail("handler never called")
        assert self.input_reader._thread
        self.input_reader._thread.join()
        self.update_mock.assert_not_called()

    def test_update_handler_true(self) -> None:
        """Test that an update is run if the handler succeeds."""
        self.update_handler_mock.return_value = True
        self.process_mock.return_value = [self.update_handler_mock]
        self.input_reader.start()
        if not self.update_handler_called.wait(timeout=1.0):
            self.fail("handler never called")
        if not self.update_called.wait(timeout=1.0):
            self.fail("update never called")
        assert self.input_reader._thread
        self.input_reader._thread.join()


class TestUpdateRunner(TestCase):
    def setUp(self) -> None:
        self.output_file = StringIO()
        self.output_writer = OutputWriter(self.output_file, [])
        self.handler_mock = Mock()
        self.update_mock = self.enterContext(patch("swaystatus.threading.OutputWriter.update", autospec=True))
        self.handler_called = Event()
        self.update_called = Event()

        def handler_side_effect(*args, **kwargs):
            self.handler_called.set()
            return DEFAULT

        self.handler_mock.side_effect = handler_side_effect

        def update_side_effect(*args, **kwargs):
            self.update_called.set()

        self.update_mock.side_effect = update_side_effect

    def test_handler_false(self) -> None:
        """Test that an update is not run if the handler fails."""
        self.handler_mock.return_value = False
        update_runner = UpdateRunner(self.output_writer, self.handler_mock)
        update_runner.start()
        assert update_runner._thread
        if not self.handler_called.wait(timeout=1.0):
            self.fail("handler never called")
        update_runner._thread.join(timeout=5.0)
        self.update_mock.assert_not_called()

    def test_handler_true(self) -> None:
        """Test that an update is run if the handler succeeds."""
        self.handler_mock.return_value = True
        update_runner = UpdateRunner(self.output_writer, self.handler_mock)
        update_runner.start()
        assert update_runner._thread
        if not self.handler_called.wait(timeout=1.0):
            self.fail("handler never called")
        if not self.update_called.wait(timeout=1.0):
            self.fail("update never called")
        update_runner._thread.join(timeout=5.0)


if __name__ == "__main__":
    main()
