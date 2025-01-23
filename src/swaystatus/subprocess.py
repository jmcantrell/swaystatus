from subprocess import Popen, PIPE
from threading import Thread


class PopenStreamHandler(Popen):
    """
    Just like `Popen`, but handle stdout and stderr output in dedicated
    threads.
    """

    def __init__(self, stdout_handler, stderr_handler, *args, **kwargs):
        def proxy(context, handler):
            with context as lines:
                for line in lines:
                    handler(line)

        kwargs["stdout"] = PIPE
        kwargs["stderr"] = PIPE

        super().__init__(*args, **kwargs)

        Thread(target=proxy, args=[self.stdout, stdout_handler]).start()
        Thread(target=proxy, args=[self.stderr, stderr_handler]).start()
