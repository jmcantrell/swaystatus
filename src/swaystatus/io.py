import locale
import sys
from signal import SIGINT, SIGTERM, SIGUSR1, Signals, signal
from threading import Event, Thread

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
        status_line = self.output_generator.process(self.file)
        while self._running.is_set():
            next(status_line)
            self._tick.clear()
            self._tick.wait(self.interval)


class InputReader(Thread):
    daemon = True
    file = sys.stdin

    def __init__(self, input_delegator: InputDelegator, output_writer: OutputWriter) -> None:
        super().__init__(name="input")
        self.input_delegator = input_delegator
        self.output_writer = output_writer

    def run(self) -> None:
        logger.info("Starting to read input...")
        for event in self.input_delegator.process(self.file):
            logger.debug(f"Processed click event: {event}")
            self.output_writer.update()


def start(config: Config) -> None:
    locale.setlocale(locale.LC_ALL, "")

    logger.debug(f"Using configuration: {config!r}")

    elements = list(config.elements)

    output_generator = OutputGenerator(elements, config.click_events)
    output_writer = OutputWriter(output_generator, config.interval)

    if config.click_events:
        input_delegator = InputDelegator(elements)
        input_reader = InputReader(input_delegator, output_writer)

    def update(sig, frame):
        logger.info(f"Signal was sent to update: {Signals(sig).name} ({sig})")
        logger.debug(f"Current stack frame: {frame}")
        output_writer.update()

    signal(SIGUSR1, update)

    def shutdown(sig, frame):
        logger.info(f"Signal was sent to shutdown: {Signals(sig).name} ({sig})")
        logger.debug(f"Current stack frame: {frame}")
        output_writer.stop()

    signal(SIGINT, shutdown)
    signal(SIGTERM, shutdown)

    if config.click_events:
        input_reader.start()

    output_writer.start()
