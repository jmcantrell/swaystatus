from typing import Iterable

from .element import BaseElement
from .input import InputProcessor
from .logging import logger
from .output import OutputProcessor
from .threading import InputReader, OutputWriter


class Daemon:
    """Coordinator of input and output."""

    def __init__(self, elements: Iterable[BaseElement], interval: float, click_events: bool) -> None:
        self.output_writer = OutputWriter(OutputProcessor(elements, click_events=click_events), interval)
        self.input_reader = InputReader(InputProcessor(elements), self.output_writer) if click_events else None

    def update(self) -> None:
        self.output_writer.update()

    def stop(self) -> None:
        logger.info("stopping daemon")
        self.output_writer.stop()

    def start(self) -> None:
        logger.info("starting daemon")
        if self.input_reader:
            self.input_reader.start()
        self.output_writer.start()


__all__ = [Daemon.__name__]
