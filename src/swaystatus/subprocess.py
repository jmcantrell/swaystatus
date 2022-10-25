from threading import Thread
from subprocess import Popen, PIPE


class PopenStreamHandler(Popen):
    """
    Just like `Popen`, but handle stdout and stderr output in dedicated
    threads.
    """

    @staticmethod
    def _proxy_lines(pipe, handler):
        with pipe:
            for line in pipe:
                handler(line)

    def __init__(self, stdout_handler, stderr_handler, *args, **kwargs):
        kwargs["stdout"] = PIPE
        kwargs["stderr"] = PIPE
        super().__init__(*args, **kwargs)
        Thread(target=self._proxy_lines, args=[self.stdout, stdout_handler]).start()
        Thread(target=self._proxy_lines, args=[self.stderr, stderr_handler]).start()
