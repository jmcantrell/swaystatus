import os
from subprocess import Popen, PIPE
from types import MethodType
from threading import Thread
from .logging import logger


class PopenLogged(Popen):
    @staticmethod
    def _proxy_lines(pipe, handler):
        with pipe:
            for line in pipe:
                handler(line)

    def __init__(self, stdout_handler, stderr_handler, *args, **kwargs):
        kwargs["stdout"] = PIPE
        kwargs["stderr"] = PIPE
        super(self.__class__, self).__init__(*args, **kwargs)
        Thread(target=self._proxy_lines, args=[self.stdout, stdout_handler]).start()
        Thread(target=self._proxy_lines, args=[self.stderr, stderr_handler]).start()


class Element:
    name = None

    def __init__(self, *args, **kwargs):
        super().__init__()

        self.name = kwargs.get("name", self.name)
        self.instance = kwargs.get("instance")
        self.env = kwargs.get("env", {})
        self.intervals = []

        for button, handler in kwargs.get("on_click", {}).items():
            self._set_on_click_handler(button, handler)

    def __str__(self):
        if not self.name:
            return super().__str__()

        args = [self.name]

        if self.instance:
            args.append(self.instance)

        return ":".join(args)

    def _set_on_click_handler(self, button, handler):
        if not callable(handler):

            def method(self, event):
                env = os.environ.copy()
                env.update(self.env)
                env.update({key: str(value if value is not None else "") for key, value in event.items()})

                def create_handler(send):
                    def handler(line):
                        msg = str(line, "utf-8").strip()
                        send(f"Output from {self} mouse button {button} handler: {msg}")

                    return handler

                stdout = create_handler(logger.info)
                stderr = create_handler(logger.error)

                logger.info(f"Executing module {self} click handler (button {button}, shell)")
                return PopenLogged(stdout, stderr, handler, shell=True, env=env)

        else:

            def method(self, event):
                logger.info(f"Executing module {self} click handler (button {button}, function)")
                return handler(event)

        setattr(self, f"on_click_{button}", MethodType(method, self))
        logger.debug(f"Module {self} set click handler for button {button}: {handler}")

    def create_block(self, full_text, **params):
        block = {"full_text": full_text}

        if self.name:
            block["name"] = self.name

        if self.instance:
            block["instance"] = self.instance

        block.update(params)

        return block

    def set_interval(self, seconds, options=None):
        logger.info(f"Module {self} is setting interval for {seconds}s: {options!r}")
        self.intervals.append((seconds, options))

    def on_interval(self, options=None):
        pass

    def on_update(self, output):
        pass

    def on_click(self, event):
        try:
            return getattr(self, f"on_click_{event['button']}")(event)
            self.updater.update()
        except AttributeError:
            pass
