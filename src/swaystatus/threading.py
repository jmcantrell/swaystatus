import sys
from subprocess import Popen
from threading import Event, Thread
from typing import Callable

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
        logger.info("updating status bar")
        self._tick.set()

    def stop(self) -> None:
        logger.info("stopping output")
        self._running.clear()
        self._tick.set()

    def start(self) -> None:
        logger.info("starting output")
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
        logger.info("starting input")
        for event, handler_result in self.input_delegator.process(self.file):
            if isinstance(handler_result, Popen):
                logger.debug(f"waiting on handler process for {event}")
                UpdateWaiter(lambda: handler_result.wait() == 0, self.output_writer).start()
            elif callable(handler_result):
                logger.debug(f"waiting on handler function for {event}")
                UpdateWaiter(handler_result, self.output_writer).start()
            elif handler_result:
                self.output_writer.update()


class UpdateWaiter(Thread):
    daemon = True

    def __init__(self, wait: Callable[[], bool], output_writer: OutputWriter) -> None:
        super().__init__(name="update")
        self.wait = wait
        self.output_writer = output_writer

    def run(self) -> None:
        if self.wait():
            self.output_writer.update()
