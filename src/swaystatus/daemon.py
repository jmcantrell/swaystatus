"""
The daemon manages input and output streams.

After starting, the daemon responds to the following signals:

SIGINT, SIGTERM
    Shut down gracefully.

SIGSTOP
    Suspend output (sent by swaybar when hidden).

SIGCONT
    Resume and immediately refresh output (sent by swaybar when unhidden).

SIGUSR1
    Immediately refresh output.
"""

from collections.abc import Callable, Sequence
from signal import SIGCONT, SIGINT, SIGTERM, SIGUSR1, Signals, signal
from types import FrameType
from typing import Any

from .element import BaseElement
from .input import InputDriver, InputProcessor
from .logger import logger
from .output import OutputDriver, OutputProcessor

SIGNALS_UPDATE = [SIGCONT, SIGUSR1]
SIGNALS_SHUTDOWN = [SIGINT, SIGTERM]


type Number = float | int
type Callback = Callable[..., Any]


class Daemon:
    """Manager of input and output streams."""

    def __init__(self, elements: Sequence[BaseElement], interval: Number | None, click_events: bool) -> None:
        self._output_driver = OutputDriver(OutputProcessor(elements, click_events), interval)
        self._input_driver = InputDriver(InputProcessor(elements, self.update)) if click_events else None

    def register_signals(self) -> None:
        for signum in SIGNALS_UPDATE:
            register_signal(signum, self.update)
        for signum in SIGNALS_SHUTDOWN:
            register_signal(signum, self.shutdown)

    def update(self) -> None:
        self._output_driver.next()

    def start(self) -> None:
        self.register_signals()
        self._output_driver.next()
        self._output_driver.start()
        if self._input_driver:
            self._input_driver.start()

    def stop(self) -> None:
        self._output_driver.stop()

    def join(self, timeout: Number | None = None) -> None:
        self._output_driver.join(timeout=timeout)

    def shutdown(self) -> None:
        self.stop()
        self.join(timeout=5.0)


def register_signal(signum: int, callback: Callback) -> None:
    def handle_signal(sig: int, frame: FrameType | None) -> None:  # pragma: no cover
        logger.info("received signal %s (%d)", Signals(sig).name, sig)
        logger.debug("current stack frame %r", frame)
        callback()

    signal(signum, handle_signal)


__all__ = [Daemon.__name__]
