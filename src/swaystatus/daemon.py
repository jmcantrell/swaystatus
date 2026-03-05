"""Manage input and output for swaystatus."""

import sys
from typing import Iterable

from .element import BaseElement
from .threading import InputReader, OutputWriter


class Daemon:
    """Coordinator of input and output."""

    def __init__(self, elements: Iterable[BaseElement], interval: float | None = None, click_events=False) -> None:
        self._output_writer = OutputWriter(sys.stdout, elements, interval=interval, click_events=click_events)
        self._input_reader = InputReader(sys.stdin, elements, self._output_writer) if click_events else None

    def update(self) -> None:
        self._output_writer.update()

    def start(self) -> None:
        self._output_writer.start()
        if self._input_reader:
            self._input_reader.start()

    def stop(self) -> None:
        self._output_writer.stop()

    def join(self, timeout: float | None = None) -> None:
        self._output_writer.join(timeout=timeout)

    def is_alive(self) -> bool:
        return self._output_writer.is_alive()


__all__ = [Daemon.__name__]
