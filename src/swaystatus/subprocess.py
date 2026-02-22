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
    """Just like `Popen`, but log stdout and stderr using dedicated threads."""

    def __init__(self, command: ShellCommand, prefix="output from shell command") -> None:
        def prefixed(line: str) -> str:
            return f"{prefix}: {line.strip()}"

        def stdout_handler(line: str) -> None:
            logger.debug(prefixed(line))

        def stderr_handler(line: str) -> None:
            logger.error(prefixed(line))

        super().__init__(command, stdout=PIPE, stderr=PIPE, shell=True, text=True)

        assert self.stdout and self.stderr

        ProxyThread(self.stdout, stdout_handler).start()
        ProxyThread(self.stderr, stderr_handler).start()
