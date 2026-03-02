"""Input/output management for swaystatus."""

import sys
from typing import Iterable

from .element import BaseElement
from .logging import logger
from .threading import InputReader, OutputWriter


class Daemon:
    """Coordinator of input and output."""

    def __init__(self, elements: Iterable[BaseElement], interval: float | None, click_events: bool) -> None:
        self._output_writer = OutputWriter(sys.stdout, elements, interval=interval, click_events=click_events)
        self._input_reader = InputReader(sys.stdin, elements, self._output_writer) if click_events else None

    def update(self) -> None:
        self._output_writer.update()

    def stop(self) -> None:
        logger.info("stopping daemon")
        self._output_writer.stop()

    def start(self) -> None:
        logger.info("starting daemon")
        if self._input_reader:
            self._input_reader.start()
        self._output_writer.start()


__all__ = [Daemon.__name__]
