from subprocess import PIPE, Popen
from threading import Thread
from typing import Callable, Iterator

from .logging import logger
from .typing import ShellCommand


class ProxyThread[T](Thread):
    """Dedicated thread for handling items from a generator."""

    source: Iterator[T]
    handler: Callable[[T], None]

    def __init__(self, source: Iterator[T], handler: Callable[[T], None]) -> None:
        super().__init__()
        self.source = source
        self.handler = handler

    def run(self) -> None:
        for item in self.source:
            self.handler(item)


class ShellCommandProcess(Popen):
    """Run a shell command, logging stdout and stderr."""

    def __init__(self, command: ShellCommand) -> None:
        super().__init__(command, stdout=PIPE, stderr=PIPE, shell=True, text=True)
        assert self.stdout and self.stderr
        ProxyThread(self.stdout, logger.debug).start()
        ProxyThread(self.stderr, logger.error).start()
