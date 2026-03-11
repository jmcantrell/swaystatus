"""Manage input and output for swaystatus."""

import sys

from .input import InputDriver, InputProcessor
from .output import OutputDriver, OutputProcessor
from .status_line import StatusLine


class Daemon:
    """Coordinator of input and output."""

    def __init__(
        self,
        status_line: StatusLine,
        interval: float | int | None,
        click_events: bool,
    ) -> None:
        self._output_driver = OutputDriver(
            OutputProcessor(
                sys.stdout,
                status_line,
                click_events,
            ),
            interval,
        )
        self._input_driver = (
            InputDriver(
                InputProcessor(
                    sys.stdin,
                    status_line,
                    self._output_driver.tick,
                )
            )
            if click_events
            else None
        )

    def update(self) -> None:
        self._output_driver.next()

    def start(self) -> None:
        self._output_driver.next()
        self._output_driver.start()
        if self._input_driver:
            self._input_driver.start()

    def stop(self) -> None:
        self._output_driver.stop()

    def join(self, timeout: float | int | None = None) -> None:
        self._output_driver.join(timeout=timeout)

    def is_alive(self) -> bool:
        return self._output_driver.is_alive()


__all__ = [Daemon.__name__]
