"""
Application lifecycle management for swaystatus.

After startup, the process responds to the following signals:

SIGINT, SIGTERM
    Shut down gracefully.

SIGSTOP
    Suspend output (sent by swaybar when hidden).

SIGCONT
    Resume and immediately refresh output (sent by swaybar when unhidden).

SIGUSR1
    Immediately refresh output.
"""

from signal import SIGCONT, SIGINT, SIGTERM, SIGUSR1, Signals, signal
from types import FrameType
from typing import Any, Callable

from .daemon import Daemon
from .logging import logger

SIGNALS_UPDATE = [SIGCONT, SIGUSR1]
SIGNALS_SHUTDOWN = [SIGINT, SIGTERM]


class App:
    """Manager for the daemon's life cycle."""

    def __init__(self, daemon: Daemon) -> None:
        self.daemon = daemon

    def update(self) -> None:
        self.daemon.update()

    def register_signals(self) -> None:
        for signum in SIGNALS_UPDATE:
            register_signal(signum, self.update)
        for signum in SIGNALS_SHUTDOWN:
            register_signal(signum, self.shutdown)

    def start(self) -> None:
        self.register_signals()
        self.daemon.start()

    def stop(self) -> None:
        self.daemon.stop()

    def join(self, timeout: float | int | None = None) -> None:
        self.daemon.join(timeout=timeout)

    def shutdown(self) -> None:
        self.stop()
        self.join(timeout=5.0)


def register_signal(signum: int, callback: Callable[..., Any]) -> None:
    def func(sig: int, frame: FrameType | None) -> None:  # pragma: no cover
        logger.info("received signal: %s (%d)", Signals(sig).name, sig)
        logger.debug("current stack frame: %r", frame)
        callback()

    signal(signum, func)


__all__ = [App.__name__]
