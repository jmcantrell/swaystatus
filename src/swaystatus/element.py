import os
from subprocess import Popen, PIPE
from types import MethodType
from threading import Thread
from .logging import logger


class PopenStreamHandler(Popen):
    """Just like `Popen`, but handle stdout and stderr output in dedicated threads."""

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


class Element:
    """An element produces content to display in the status bar."""

    name = None

    def __init__(self, name=None, instance=None, env=None, on_click=None):
        super().__init__()

        self.name = name
        self.instance = instance
        self.env = env or {}
        self.intervals = []

        if on_click:
            for button, handler in on_click.items():
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
                return PopenStreamHandler(stdout, stderr, handler, shell=True, env=env)

        else:

            def method(self, event):
                logger.info(f"Executing module {self} click handler (button {button}, function)")
                return handler(event)

        setattr(self, f"on_click_{button}", MethodType(method, self))
        logger.debug(f"Module {self} set click handler for button {button}: {handler}")

    def create_block(self, full_text, **params):
        """Helper for creating a block of content for output to the status bar."""

        block = {"full_text": full_text}

        if self.name:
            block["name"] = self.name

        if self.instance:
            block["instance"] = self.instance

        block.update(params)

        return block

    def set_interval(self, seconds, options=None):
        """
        Set a trigger that activates periodically (can be used multiple times).

        Every `seconds` seconds call `self.on_interval` with `options` as an
        argument. It's probable that the trigger will not activate as precisely
        as might be expected, as the check that determines if it should
        activate is only done at each update loop iteration. It's recommended
        that `seconds` should be some multiple of the configured interval.
        """

        logger.info(f"Module {self} is setting interval for {seconds}s: {options!r}")
        self.intervals.append((seconds, options))

    def on_interval(self, options):
        """
        Perform some action after a previously set interval.

        An interval should be set using `self.set_interval` during
        initialization and this method should be overridden for this feature to
        be useful.
        """

        pass

    def on_update(self, output: list[dict[str, object]]):
        """
        Perform some action on every update loop iteration.

        For anything to appear on the status bar, a block should be added to
        `output` in this method. For a description of blocks, see the "BODY"
        section of swaybar-protocol(7).

        There are no requirements for the presence or absence of a block nor
        for how many are added.

        It's recommended to use `self.create_block` to create the blocks:
        >>> output.append(self.create_block("hello, world"))

        But they can also be added directly:
        >>> output.append({"full_text": "hello, world"})
        """

        pass

    def on_click(self, event: dict[str, object]):
        """
        Perform some action when a status bar block is clicked.

        If `click_events` is set to `True` in the configuration and the
        element's name attribute is set, any time the user clicks a block, this
        method will be called on the element that produced it and passed an
        event object describing the click. For a description of click events,
        see the "CLICK EVENTS" section of swaybar-protocol(7).

        If blocks are created using `self.create_block`, the name and,
        optionally, instance keys will be set automatically in the block.
        """

        try:
            return getattr(self, f"on_click_{event['button']}")(event)
        except AttributeError:
            pass
