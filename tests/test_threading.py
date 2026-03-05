import logging
from io import StringIO
from itertools import chain, repeat
from random import randint
from threading import Barrier
from typing import IO, Iterator
from unittest.mock import Mock, call

from pytest import FixtureRequest, fixture, mark
from pytest_mock import MockerFixture

from swaystatus.threading import InputReader, OutputWriter, Ticker


class TickerHarness:
    ticker: Ticker
    tick_called: Barrier
    wait_called: Barrier
    wait_mock: Mock
    stopper_is_set_mock: Mock

    def __init__(self, mocker: MockerFixture, ticker: Ticker) -> None:
        self.ticker = ticker
        self.wait_called = Barrier(2, timeout=1.0)

        def wait_side_effect(*args, **kwargs):
            self.wait_called.wait()
            return mocker.DEFAULT

        self.wait_mock = mocker.patch.object(
            self.ticker._waiter,
            "wait",
            side_effect=wait_side_effect,
        )
        self.stopper_is_set_mock = mocker.patch.object(
            self.ticker._stopper,
            "is_set",
            return_value=False,
        )
        self.tick_called = Barrier(2, timeout=1.0)

    def start(self) -> None:
        self.ticker.start(self.tick_called.wait)

    def shutdown(self) -> None:
        self.ticker.stop()
        self.ticker.join(timeout=1.0)
        assert not self.ticker.is_alive(), "thread never died"
        assert self.wait_mock.mock_calls == [call(timeout=self.ticker.interval)] * self.wait_mock.call_count


class TestTicker:
    def test_sync(self, harness: TickerHarness) -> None:
        """Test that ticking happens after waiting."""
        harness.start()
        for stopping in chain(repeat(False, randint(1, 10)), [True]):
            harness.wait_called.wait()
            harness.stopper_is_set_mock.return_value = stopping
            harness.tick_called.wait()

    @fixture(params=[None, 5.0])
    def harness(self, request: FixtureRequest, mocker: MockerFixture) -> Iterator[TickerHarness]:
        harness = TickerHarness(mocker, Ticker(interval=request.param))
        yield harness
        harness.shutdown()


class OutputWriterHarness:
    output_writer: OutputWriter
    process_mock: Mock
    process_yielded: Barrier
    process_yield_mock: Mock

    def __init__(self, mocker: MockerFixture, output_writer: OutputWriter) -> None:
        self.output_writer = output_writer
        self.process_yielded = Barrier(2, timeout=1.0)

        def process_yield_side_effect(*args, **kwargs):
            self.process_yielded.wait()
            return mocker.DEFAULT

        self.process_yield_mock = mocker.Mock(side_effect=process_yield_side_effect)

        def process_side_effect(*args, **kwargs):
            while True:
                yield self.process_yield_mock()

        self.process_mock = mocker.patch.object(
            self.output_writer._output_processor,
            "process",
            side_effect=process_side_effect,
        )

    @property
    def output_file(self) -> IO[str]:
        return self.output_writer._output_file

    def start(self) -> None:
        self.output_writer.start()

    def shutdown(self) -> None:
        self.output_writer.stop()
        self.output_writer.join(timeout=1.0)
        assert not self.output_writer.is_alive(), "thread never died"


class TestOutputWriter:
    def test_generator_start(self, harness: OutputWriterHarness) -> None:
        """Test that the output processor begins iteration."""
        harness.output_writer.start()
        harness.output_writer.stop()
        harness.process_yielded.wait()
        harness.process_mock.assert_called_once_with(harness.output_file)

    def test_sync(self, harness: OutputWriterHarness) -> None:
        """Test that the output processor yields are handled repeatedly."""
        harness.output_writer.start()
        for stopping in chain(repeat(False, randint(1, 10)), [True]):
            harness.process_yielded.wait()
            if stopping:
                harness.output_writer.stop()
            else:
                harness.output_writer.update()

    def test_yield_raises(self, harness: OutputWriterHarness, assert_log_record) -> None:
        harness.process_yield_mock.side_effect = Exception("BOOM!")
        harness.output_writer.start()
        harness.output_writer.stop()
        harness.output_writer.join(timeout=1.0)
        assert_log_record(logging.ERROR, "unhandled exception in output processor")

    @fixture
    def harness(self, mocker: MockerFixture) -> Iterator[OutputWriterHarness]:
        harness = OutputWriterHarness(mocker, OutputWriter(StringIO(), []))
        yield harness
        harness.shutdown()


class InputReaderHarness:
    input_reader: InputReader
    process_mock: Mock
    process_yielded: Barrier
    process_yield_mock: Mock
    update_handler_mock: Mock
    update_mock: Mock

    def __init__(self, mocker: MockerFixture, input_reader: InputReader) -> None:
        self.input_reader = input_reader
        self.process_yielded = Barrier(2, timeout=1.0)

        def process_yield_side_effect(*args, **kwargs):
            self.process_yielded.wait()
            return mocker.DEFAULT

        self.process_yield_mock = mocker.Mock(side_effect=process_yield_side_effect)

        def process_side_effect(*args, **kwargs):
            while True:
                yield self.process_yield_mock()

        self.process_mock = mocker.patch.object(
            input_reader._input_processor,
            "process",
            side_effect=process_side_effect,
        )
        self.update_handler_mock = Mock()
        self.update_mock = mocker.patch.object(input_reader._output_writer, "update")

    @property
    def input_file(self) -> IO[str]:
        return self.input_reader._input_file

    def start(self) -> None:
        self.input_reader.start()

    def shutdown(self) -> None:
        self.input_reader.stop()
        self.input_reader.join(timeout=1.0)
        assert not self.input_reader.is_alive(), "thread never died"


class TestInputReader:
    def test_generator_start(self, harness: InputReaderHarness) -> None:
        """Test that the input processor begins iteration."""
        harness.input_reader.start()
        harness.input_reader.stop()
        harness.process_yielded.wait()
        harness.process_mock.assert_called_once_with(harness.input_file)

    def test_sync(self, harness: InputReaderHarness) -> None:
        """Test that the input processor yields are handled repeatedly."""
        harness.input_reader.start()
        for stopping in chain(repeat(False, randint(1, 10)), [True]):
            harness.process_yielded.wait()
            if stopping:
                harness.input_reader.stop()

    def test_yield_raises(self, harness: InputReaderHarness, assert_log_record) -> None:
        harness.process_yield_mock.side_effect = Exception("BOOM!")
        harness.input_reader.start()
        harness.input_reader.stop()
        harness.input_reader.join(timeout=1.0)
        assert_log_record(logging.ERROR, "unhandled exception in input processor")

    @mark.parametrize("update", [False, True])
    def test_update(self, update: bool, harness: InputReaderHarness) -> None:
        """Test that an update is run if requested."""
        harness.process_yield_mock.return_value = update
        harness.input_reader.start()
        harness.input_reader.stop()
        harness.process_yielded.wait()
        harness.input_reader.join()
        assert harness.update_mock.call_count == int(update)

    @mark.parametrize("update", [False, True])
    def test_update_handler(self, update: bool, harness: InputReaderHarness) -> None:
        """Test that an update handler can request an update."""
        harness.update_handler_mock.return_value = update
        harness.process_yield_mock.return_value = harness.update_handler_mock
        harness.input_reader.start()
        harness.input_reader.stop()
        harness.process_yielded.wait()
        harness.input_reader.join()
        assert harness.update_mock.call_count == int(update)

    @fixture
    def harness(self, mocker: MockerFixture) -> Iterator[InputReaderHarness]:
        harness = InputReaderHarness(mocker, InputReader(StringIO(), [], OutputWriter(StringIO(), [])))
        yield harness
        harness.shutdown()
