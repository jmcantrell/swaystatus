from signal import SIGCONT, SIGINT, SIGTERM, SIGUSR1, Signals, signal
from types import FrameType

from .daemon import Daemon
from .logging import logger

SIGNALS_UPDATE = [SIGUSR1, SIGCONT]
SIGNALS_SHUTDOWN = [SIGINT, SIGTERM]


class App:
    """Manager for the daemon's lifecycle."""

    def __init__(self, daemon: Daemon) -> None:
        self.daemon = daemon

    def update(self, sig: int, frame: FrameType | None) -> None:
        logger.info("signaled to update: %s (%d)", Signals(sig).name, sig)
        logger.debug("current stack frame: %r", frame)
        self.daemon.update()

    def shutdown(self, sig: int, frame: FrameType | None) -> None:
        logger.info("signaled to shutdown: %s (%d)", Signals(sig).name, sig)
        logger.debug("current stack frame: %r", frame)
        self.daemon.stop()

    def run(self) -> None:
        for signum in SIGNALS_UPDATE:
            signal(signum, self.update)
        for signum in SIGNALS_SHUTDOWN:
            signal(signum, self.shutdown)
        self.daemon.start()


__all__ = [App.__name__]
