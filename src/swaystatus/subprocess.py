from threading import Thread
from subprocess import Popen, PIPE


def proxy_lines(pipe, handler):
    with pipe:
        for line in pipe:
            handler(line)


class PopenStreamHandler(Popen):
    """
    Just like `Popen`, but handle stdout and stderr output in dedicated
    threads.
    """

    def __init__(self, stdout_handler, stderr_handler, *args, **kwargs):
        kwargs["stdout"] = PIPE
        kwargs["stderr"] = PIPE
        super().__init__(*args, **kwargs)
        Thread(target=proxy_lines, args=[self.stdout, stdout_handler]).start()
        Thread(target=proxy_lines, args=[self.stderr, stderr_handler]).start()
