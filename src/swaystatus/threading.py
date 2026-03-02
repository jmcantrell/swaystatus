from threading import Event, Thread
from typing import IO, Callable, Iterable

from .element import BaseElement, UpdateHandler
from .input import InputProcessor
from .logging import logger
from .output import OutputProcessor
from .time import Elapsed


class Ticker:
    """Run a function periodically in a dedicated thread."""

    def __init__(self, interval: float | None = None, name: str | None = None) -> None:
        self.interval = interval
        self.name = name
        self._waiter = Event()
        self._stopper = Event()
        self._thread: Thread | None = None

    def tick(self) -> None:
        self._waiter.set()

    def stop(self) -> None:
        self._stopper.set()
        self._waiter.set()
        if self._thread:
            self._thread.join()

    def start(self, on_tick: Callable[[], None]) -> None:
        def run() -> None:
            self._stopper.clear()
            while not self._stopper.is_set():
                on_tick()
                self._waiter.wait(timeout=self.interval)
                self._waiter.clear()

        self._thread = Thread(target=run, name=self.name)
        self._thread.start()


class OutputWriter:
    """Write status lines to an output file at a regular interval and when requested."""

    def __init__(
        self,
        file: IO[str],
        elements: Iterable[BaseElement],
        interval: float | None = None,
        click_events=False,
    ) -> None:
        self._file = file
        self._elements = elements
        self._output_processor = OutputProcessor(elements, click_events=click_events)
        self._ticker = Ticker(interval=interval, name="output")

    def update(self) -> None:
        logger.info("updating output")
        self._ticker.tick()

    def stop(self) -> None:
        logger.info("stopping output")
        self._ticker.stop()

    def start(self) -> None:
        elapsed = Elapsed()
        status_lines = self._output_processor.process(self._file)

        def on_tick() -> None:
            with elapsed:
                status_line = next(status_lines)
            logger.debug("generated status line in %0.2f seconds: %r", elapsed.seconds, status_line)

        logger.info("starting output")
        self._ticker.start(on_tick)


class InputReader:
    """Send click events from an input file to a targed element and handle results."""

    def __init__(self, file: IO[str], elements: Iterable[BaseElement], output_writer: OutputWriter) -> None:
        self.file = file
        self._input_processor = InputProcessor(elements)
        self._output_writer = output_writer
        self._thread: Thread | None = None

    def start(self) -> None:
        def run() -> None:
            logger.info("starting input")
            for update in self._input_processor.process(self.file):
                if callable(update):
                    UpdateRunner(self._output_writer, update).start()
                elif update:
                    self._output_writer.update()

        self._thread = Thread(target=run, name="input", daemon=True)
        self._thread.start()


class UpdateRunner:
    """Update the status line only after successful handler completion."""

    def __init__(self, output_writer: OutputWriter, update_handler: UpdateHandler) -> None:
        self._output_writer = output_writer
        self._update_handler = update_handler
        self._thread: Thread | None = None

    def start(self) -> None:
        def run() -> None:
            if self._update_handler():
                self._output_writer.update()

        self._thread = Thread(target=run, name="update", daemon=True)
        self._thread.start()


__all__ = [
    OutputWriter.__name__,
    InputReader.__name__,
]
