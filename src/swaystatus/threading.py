import sys
from subprocess import Popen
from threading import Event, Thread

from .element import ClickHandlerResult
from .input import InputProcessor
from .logging import logger
from .output import OutputProcessor


class OutputWriter:
    """Write status lines to an output file at a regular interval and when requested."""

    file = sys.stdout

    def __init__(self, output_processor: OutputProcessor, interval: float) -> None:
        self.output_processor = output_processor
        self.interval = interval
        self._tick = Event()
        self._running = Event()

    def update(self) -> None:
        logger.info("updating status bar")
        self._tick.set()

    def stop(self) -> None:
        logger.info("stopping output")
        self._running.clear()
        self._tick.set()

    def start(self) -> None:
        logger.info("starting output")
        self._running.set()
        for blocks in self.output_processor.process(self.file):
            logger.debug(f"processed output: {blocks}")
            self._tick.clear()
            self._tick.wait(self.interval)
            if not self._running.is_set():
                break


class InputReader(Thread):
    """Send click events from an input file to a targed element and handle results."""

    daemon = True
    file = sys.stdin

    def __init__(self, input_processor: InputProcessor, output_writer: OutputWriter) -> None:
        super().__init__(name="input")
        self.input_processor = input_processor
        self.output_writer = output_writer

    def run(self) -> None:
        logger.info("starting input")
        for click_event, element, handler_result in self.input_processor.process(self.file):
            UpdateHandler(self.output_writer, handler_result).start()


class UpdateHandler(Thread):
    """Update the status line only after successful handler completion."""

    daemon = True

    def __init__(self, output_writer: OutputWriter, handler_result: ClickHandlerResult) -> None:
        super().__init__(name="update")
        self.output_writer = output_writer
        self.handler_result = handler_result

    def wait(self) -> bool:
        return (
            (isinstance(self.handler_result, Popen) and self.handler_result.wait() == 0)
            or (callable(self.handler_result) and self.handler_result())
            or bool(self.handler_result)
        )

    def run(self) -> None:
        if self.wait():
            self.output_writer.update()
