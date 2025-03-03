from subprocess import PIPE, Popen
from threading import Thread
from typing import IO, Callable


class PopenStreamHandler(Popen):
    """Just like `Popen`, but handle stdout and stderr output in dedicated threads."""

    def __init__(self, stdout_handler, stderr_handler, *args, **kwargs) -> None:
        kwargs["stdout"] = kwargs["stderr"] = PIPE
        super().__init__(*args, **kwargs)
        assert self.stdout and self.stderr
        ProxyThread(self.stdout, stdout_handler).start()
        ProxyThread(self.stderr, stderr_handler).start()


class ProxyThread(Thread):
    """Thread that sends it's input to a function."""

    def __init__(self, source: IO[str], handler: Callable[[str], None]) -> None:
        super().__init__()
        self.source = source
        self.handler = handler

    def run(self) -> None:
        with self.source as lines:
            for line in lines:
                self.handler(line.strip())
