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

SIGNALS_UPDATE = [SIGUSR1, SIGCONT]
SIGNALS_SHUTDOWN = [SIGINT, SIGTERM]


def register_signal(signum: int, callback: Callable[..., Any]) -> None:
    def func(sig: int, frame: FrameType | None) -> None:
        logger.info("received signal: %s (%d)", Signals(sig).name, sig)
        logger.debug("current stack frame: %r", frame)
        callback()

    signal(signum, func)


class App:
    """Manager for the daemon's life cycle."""

    def __init__(self, daemon: Daemon) -> None:
        self.daemon = daemon

    def update(self) -> None:
        self.daemon.update()

    def shutdown(self) -> None:
        self.daemon.stop()

    def register_signals(self) -> None:
        logger.debug("HERE")
        for signum in SIGNALS_UPDATE:
            register_signal(signum, self.update)
        for signum in SIGNALS_SHUTDOWN:
            register_signal(signum, self.shutdown)

    def run(self) -> None:
        self.register_signals()
        self.daemon.start()


__all__ = [App.__name__]
