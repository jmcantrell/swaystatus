"""
An element produces blocks of content to display in the status bar.

When the status bar is running, every configured element will be prompted for
blocks at the configured interval. Once every element has replied, all of the
collected blocks are encoded and sent to the bar via stdout.
"""

import os
from functools import cached_property
from subprocess import PIPE, Popen
from threading import Thread
from types import MethodType
from typing import IO, Callable, Iterator

from .block import Block
from .click_event import ClickEvent
from .logging import logger

type StreamHandler = Callable[[str], None]
type ClickHandler = str | list[str] | Callable[[ClickEvent], None]


class ProxyThread(Thread):
    """Thread that sends it's input to a handler."""

    def __init__(self, source: IO[str], handler: StreamHandler) -> None:
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


class BaseElement:
    """
    A base class for constructing elements for the status bar.

    The subclass must be named `Element` and be contained in a module file
    whose name will be used by swaystatus to identify it. For example, if there
    is a file named `clock.py` in a modules package, the class will have an
    attribute `name` set to "clock".

    The `blocks` method should be overridden to produce output. There is no
    restriction or requirement on the number of blocks an element instance
    produces on each invocation of the method.

    A hypothetical clock module file could contain the following:

        >>> from time import strftime
        >>> from typing import Iterator
        >>> from swaystatus import BaseElement, Block
        >>> class Element(BaseElement):
        >>>     def blocks(self) -> Iterator[Block]:
        >>>         yield self.create_block(strftime("%c"))

    The most direct way to use the module would be to add it to the
    configuration directory in a `modules` package:

        $XDG_CONFIG_HOME/swaystatus/
        ├── config.toml      # <= configuration goes here
        └── modules/
            ├── __init__.py  # <= necessary, to mark this as a package
            └── clock.py     # <= module goes here

    Enable the module by adding it to the configuration file:

        order = ["clock"]

    If the clock should respond to a left mouse button click by running a shell
    command, enable click events and add a click handler to the settings for
    that module:

        order = ["clock"]

        click_events = true

        [settings.clock]
        on_click.1 = "foot --hold cal"

    Maybe there needs to be an additional clock that always shows a specific timezone:

        order = ["clock", "clock:home"]

        click_events = true

        [settings.clock]
        on_click.1 = "foot --hold cal"

        [settings."clock:home".env]
        TZ = 'Asia/Tokyo'

    The "name:instance" syntax allows multiple instances of the same module,
    each having their own settings.
    """

    name: str
    instance: str | None = None

    def __init__(
        self,
        *,
        env: dict[str, str] | None = None,
        on_click: dict[int, ClickHandler] | None = None,
    ) -> None:
        """
        Intialize a new status bar content producer.

        The dict `env` will be added to the execution environment of any click
        handler.

        The dict `on_click` maps pointer button numbers to click handlers (i.e.
        a function or shell command) which take precedence over any already
        defined on the class.

        When subclassing, there could be more keyword arguments passed,
        depending on its settings in the configuration file.

        To illustrate, let's change the clock example from earlier to allow
        configuration of how the element displays the time. Add a constructor
        that accepts a keyword argument, and change the `blocks` method to use
        the setting:

            >>> from time import strftime
            >>> from typing import Iterator
            >>> from swaystatus import BaseElement, Block
            >>> class Element(BaseElement):
            >>>     def __init__(self, full_text="%c", **kwargs) -> None:
            >>>         super().__init__(**kwargs)
            >>>         self.full_text = full_text
            >>>     def blocks(self) -> Iterator[Block]:
            >>>         yield self.create_block(strftime(self.full_text))

        Without any further changes, it will behave as it did originally, but
        now it can be configured by adding something like the following to the
        configuration file:

            [settings.clock]
            full_text = "The time here is: %r"

        If there are other instances of the module, they will inherit the
        setting, but it can be overridden:

            [settings."clock:home"]
            full_text = "The time at home is: %r"
        """
        self.env = env or {}
        if on_click:
            for button, handler in on_click.items():
                self.set_on_click_handler(button, handler)

    def __str__(self) -> str:
        return self.key

    @cached_property
    def key(self) -> str:
        """Return a string uniquely identifying this element instance."""
        return f"{self.name}:{self.instance}" if self.instance else self.name

    def blocks(self) -> Iterator[Block]:
        """
        Yield blocks of content to display on the status bar.

        To create a block, it's recommended to use `self.create_block` so that
        the block has the proper name and instance set:

            >>> from typing import Iterator
            >>> from swaystatus import BaseElement, Block
            >>> class Element(BaseElement):
            >>>     def blocks(self) -> Iterator[Block]:
            >>>         yield self.create_block("Howdy!")
        """
        raise NotImplementedError

    def create_block(self, full_text: str, **kwargs) -> Block:
        """Create a block of content associated with this element."""
        if self.instance is not None:
            kwargs["instance"] = self.instance
        return Block(name=self.name, full_text=full_text, **kwargs)

    def on_click(self, event: ClickEvent) -> None:
        """Perform some action when a status bar block is clicked."""
        try:
            getattr(self, f"on_click_{event.button}")(event)
        except AttributeError:
            pass

    def set_on_click_handler(self, button: int, handler: ClickHandler):
        """
        Add a method to this instance that calls `handler` when this element
        is clicked with the pointer `button`.

        The handler can be a function that accepts a `ClickEvent` as the first
        (and only) positional argument. It can also be a command compatible
        with the various `subprocess` functions, i.e. a `str` or `list[str]`
        representing a shell command.

        This is mainly a convenience method that handles binding a regular
        function as a method and logging everything.
        """
        if callable(handler):

            def method(self, event: ClickEvent):
                logger.info(f"Executing {self} module function click handler for button {button}")
                environ_save = os.environ.copy()
                os.environ.update(self.env)
                try:
                    handler(event)
                finally:
                    os.environ.update(environ_save)
        else:

            def method(self, event: ClickEvent):
                env = os.environ.copy()
                env.update(self.env)
                env.update({k: str(v) for k, v in event.dict().items()})
                logger.info(f"Executing {self} module shell command click handler for button {button}")
                PopenStreamHandler(logger.debug, logger.error, handler, shell=True, text=True, env=env).wait()

        logger.debug(f"Module {self} setting click handler: button {button} => {handler}")
        setattr(self, f"on_click_{button}", MethodType(method, self))
