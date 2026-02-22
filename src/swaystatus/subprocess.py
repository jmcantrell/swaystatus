from subprocess import PIPE, Popen
from threading import Thread
from typing import IO, Callable

from .logging import logger


class ProxyThread[T: (str, bytes)](Thread):
    source: IO[T]
    handler: Callable[[T], None]

    def __init__(self, source: IO[T], handler: Callable[[T], None]) -> None:
        super().__init__()
        self.source = source
        self.handler = handler

    def run(self) -> None:
        with self.source as lines:
            for line in lines:
                self.handler(line)


class PopenStreamHandler(Popen):
    """Just like `Popen`, but handle stdout and stderr output in dedicated threads."""

    def __init__(self, stdout_handler, stderr_handler, *args, **kwargs) -> None:
        kwargs["stdout"] = kwargs["stderr"] = PIPE
        super().__init__(*args, **kwargs)
        assert self.stdout and self.stderr
        ProxyThread(self.stdout, stdout_handler).start()
        ProxyThread(self.stderr, stderr_handler).start()


class PopenLogged(PopenStreamHandler):
    """Just like `Popen`, but log stdout and stderr using dedicated threads."""

    def __init__(self, prefix: str, *args, **kwargs) -> None:
        def prefixed(func: Callable[[str], None]) -> Callable[[str], None]:
            def inner(line: str) -> None:
                func(f"{prefix}: {line.strip()}")

            return inner

        super().__init__(
            prefixed(logger.debug),
            prefixed(logger.error),
            *args,
            **kwargs,
            text=True,
        )
