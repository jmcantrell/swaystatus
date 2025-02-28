import locale
import sys
from signal import SIGCONT, SIGINT, SIGTERM, SIGUSR1, Signals, signal
from subprocess import Popen
from threading import Event, Thread
from typing import Callable

from .config import Config
from .input import InputDelegator
from .logging import logger
from .output import OutputGenerator


class OutputWriter:
    file = sys.stdout

    def __init__(self, output_generator: OutputGenerator, interval: float) -> None:
        self.output_generator = output_generator
        self.interval = interval
        self._tick = Event()
        self._running = Event()

    def update(self) -> None:
        self._tick.set()

    def stop(self) -> None:
        self._running.clear()
        self._tick.set()

    def start(self) -> None:
        logger.info("Starting to write output...")
        self._running.set()
        for blocks in self.output_generator.process(self.file):
            self._tick.clear()
            self._tick.wait(self.interval)
            if not self._running.is_set():
                break


class InputReader(Thread):
    daemon = True
    file = sys.stdin

    def __init__(self, input_delegator: InputDelegator, output_writer: OutputWriter) -> None:
        super().__init__(name="input")
        self.input_delegator = input_delegator
        self.output_writer = output_writer

    def run(self) -> None:
        logger.info("Starting to read input...")
        for event, result in self.input_delegator.process(self.file):
            if isinstance(result, Popen):
                UpdaterWaiter(lambda: result.wait() == 0, self.output_writer).start()
            elif callable(result):
                UpdaterWaiter(result, self.output_writer).start()
            elif result:
                self.output_writer.update()


class UpdaterWaiter(Thread):
    daemon = True

    def __init__(self, wait: Callable[[], bool], output_writer: OutputWriter) -> None:
        super().__init__(name="update")
        self.wait = wait
        self.output_writer = output_writer

    def run(self) -> None:
        if self.wait():
            self.output_writer.update()


def start(config: Config) -> None:
    locale.setlocale(locale.LC_ALL, "")

    output_generator = OutputGenerator(config.elements, config.click_events)
    output_writer = OutputWriter(output_generator, config.interval)

    if config.click_events:
        input_delegator = InputDelegator(config.elements)
        input_reader = InputReader(input_delegator, output_writer)

    def update(sig, frame):
        logger.info(f"Signal was sent to update: {Signals(sig).name} ({sig})")
        logger.debug(f"Current stack frame: {frame!r}")
        output_writer.update()

    signal(SIGUSR1, update)
    signal(SIGCONT, update)

    def shutdown(sig, frame):
        logger.info(f"Signal was sent to shutdown: {Signals(sig).name} ({sig})")
        logger.debug(f"Current stack frame: {frame!r}")
        output_writer.stop()

    signal(SIGINT, shutdown)
    signal(SIGTERM, shutdown)

    if config.click_events:
        input_reader.start()

    output_writer.start()


__all__ = [start.__name__]
