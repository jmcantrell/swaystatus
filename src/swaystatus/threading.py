from threading import Event, Thread
from typing import IO, Any, Callable, Iterable

from .element import BaseElement, UpdateHandler
from .input import InputProcessor
from .logging import logger
from .output import OutputProcessor
from .timing import Elapsed


class OutputWriter:
    """Write status lines to an output file at a regular interval and when requested."""

    def __init__(
        self,
        output_file: IO[str],
        elements: Iterable[BaseElement],
        interval: float | None = None,
        click_events=False,
    ) -> None:
        self._output_file = output_file
        self._elements = elements
        self._output_processor = OutputProcessor(elements, click_events=click_events)
        self._ticker = Ticker(interval=interval, name="output")

    def start(self) -> None:
        elapsed = Elapsed()
        status_lines = self._output_processor.process(self._output_file)

        def on_tick() -> None:
            try:
                with elapsed:
                    status_line = next(status_lines)
            except Exception:
                logger.exception("unhandled exception in output processor")
                return
            logger.debug(
                "generated status line in %0.2f seconds: %r",
                elapsed.seconds,
                status_line,
            )

        logger.info("starting output")
        self._ticker.tick()
        self._ticker.start(on_tick)

    def update(self) -> None:
        logger.info("updating output")
        self._ticker.tick()

    def stop(self) -> None:
        logger.info("stopping output")
        self._ticker.stop()

    def is_alive(self) -> bool:
        return self._ticker.is_alive()

    def join(self, timeout: float | None = None) -> None:
        self._ticker.join(timeout=timeout)


class Ticker:
    """Run a function periodically in a dedicated thread."""

    def __init__(self, interval: float | None = None, name: str | None = None) -> None:
        self.interval = interval
        self.name = name
        self._waiter = Event()
        self._stopper = Event()
        self._thread: Thread | None = None

    def start(self, on_tick: Callable[..., Any]) -> None:
        def run() -> None:
            self._stopper.clear()
            while not self._stopper.is_set():
                self._waiter.wait(timeout=self.interval)
                self._waiter.clear()
                on_tick()

        self._thread = Thread(target=run, name=self.name)
        self._thread.start()

    def tick(self) -> None:
        self._waiter.set()

    def stop(self) -> None:
        self._stopper.set()
        self._waiter.set()

    def join(self, timeout: float | None = None) -> None:
        if self._thread:
            self._thread.join(timeout=timeout)

    def is_alive(self) -> bool:
        return self._thread.is_alive() if self._thread else False


class InputReader:
    """Send click events from an input file to a targed element and handle results."""

    def __init__(self, file: IO[str], elements: Iterable[BaseElement], output_writer: OutputWriter) -> None:
        self._input_file = file
        self._input_processor = InputProcessor(elements)
        self._output_writer = output_writer
        self._stopper = Event()
        self._thread: Thread | None = None

    def start(self) -> None:
        def run() -> None:
            logger.info("starting input")
            updates = self._input_processor.process(self._input_file)
            while not self._stopper.is_set():
                try:
                    update = next(updates)
                except Exception:
                    logger.exception("unhandled exception in input processor")
                    continue
                if callable(update):
                    UpdateRunner(self._output_writer, update).start()
                elif update:
                    self._output_writer.update()

        self._thread = Thread(target=run, name="input", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stopper.set()

    def join(self, timeout: float | None = None) -> None:
        if self._thread:
            self._thread.join(timeout=timeout)

    def is_alive(self) -> bool:
        return self._thread.is_alive() if self._thread else False


class UpdateRunner:
    """Update the status line only after successful handler completion."""

    def __init__(self, output_writer: OutputWriter, update_handler: UpdateHandler) -> None:
        self._output_writer = output_writer
        self._update_handler = update_handler
        self._thread: Thread | None = None

    def start(self) -> None:
        def run() -> None:
            try:
                if self._update_handler():
                    self._output_writer.update()
            except Exception:
                logger.exception("unhandled exception in update handler")

        self._thread = Thread(target=run, name="update", daemon=True)
        self._thread.start()

    def join(self, timeout: float | None = None) -> None:
        if self._thread:
            self._thread.join(timeout=timeout)

    def is_alive(self) -> bool:
        return self._thread.is_alive() if self._thread else False
