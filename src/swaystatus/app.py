from signal import SIGCONT, SIGINT, SIGTERM, SIGUSR1, Signals, signal
from types import FrameType

from .daemon import Daemon
from .logging import logger


class App:
    def __init__(self, daemon: Daemon) -> None:
        self.daemon = daemon

    def update(self, sig: int, frame: FrameType | None) -> None:
        logger.info(f"signaled to update: {Signals(sig).name} ({sig})")
        logger.debug(f"current stack frame: {frame!r}")
        self.daemon.update()

    def shutdown(self, sig: int, frame: FrameType | None) -> None:
        logger.info(f"signaled to shutdown: {Signals(sig).name} ({sig})")
        logger.debug(f"current stack frame: {frame!r}")
        self.daemon.stop()

    def run(self) -> None:
        signal(SIGUSR1, self.update)
        signal(SIGCONT, self.update)
        signal(SIGINT, self.shutdown)
        signal(SIGTERM, self.shutdown)
        self.daemon.start()


__all__ = [App.__name__]
