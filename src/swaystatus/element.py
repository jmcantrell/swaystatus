"""
An element produces blocks of content to display in the status bar.

When the status bar is running, every configured element will be prompted for
blocks at the configured interval. Once every element has replied, all of the
collected blocks are encoded and sent to the bar via stdout.
"""

import os
from subprocess import PIPE, Popen
from threading import Thread
from types import MethodType
from typing import IO, Callable, Iterator, Self

from .block import Block
from .click_event import ClickEvent
from .logging import logger

type ClickHandler[T: BaseElement] = str | list[str] | Callable[[T, ClickEvent], None]


class BaseElement:
    """
    A base class for constructing elements for the status bar.

    The subclass must be named `Element` and be contained in a module file
    whose name will be used by swaystatus to identify it. For example, if there
    is a file named `clock.py` in a modules package, the class will have an
    attribute `name` set to "clock".

    The `blocks` method is called to generate output at every interval and must
    be overridden. There is no requirement regarding the number of blocks that
    are yielded, however if no blocks are yielded, nothing will be visible in
    the status bar for that element. This may be desirable if, for example, the
    module yields a block for every mounted disk and there are none mounted.

    A hypothetical clock module file might contain the following:

        >>> from time import strftime
        >>> from typing import Iterator
        >>> from swaystatus import BaseElement, Block
        >>> class Element(BaseElement):
        >>>     def blocks(self) -> Iterator[Block]:
        >>>         yield self.block(strftime("%c"))

    Enable the module by adding it to the configuration file:

        order = ["clock"]

    Let's make the clock respond to a left mouse button click by running a
    shell command. Enable click events and add a click handler to the settings
    for that module:

        order = ["clock"]

        click_events = true

        [settings.clock]
        on_click.1 = "foot --hold cal"

    Maybe there needs to be an additional clock that always shows a specific
    timezone:

        order = ["clock", "clock:home"]

        click_events = true

        [settings.clock]
        on_click.1 = "foot --hold cal"

        [settings."clock:home".env]
        TZ = 'Asia/Tokyo'

    The "name:instance" form in `order` allows multiple instances of the same
    module, each having their own settings.

    Because the module is named `clock.py`, swaystatus will set the class
    attribute `name` to "clock" for the first element ("clock" in `order`) as
    if it had been declared like:

        >>> from swaystatus import BaseElement
        >>> class Element(BaseElement):
        >>>     name = "clock"

    Because the second element ("clock:home") is using the "name:instance"
    form, it will also have the instance attribute `instance` set to "home" as
    if it had been declared like:

        >>> from swaystatus import BaseElement
        >>> class Element(BaseElement):
        >>>     name = "clock"
        >>> element = Element()
        >>> element.instance = "home"

    You should not set these attributes yourself, as it will confuse and sadden
    swaystatus, and it will propably not respond to your clicks.
    """

    name: str

    def __init__(
        self,
        *,
        instance: str | None = None,
        env: dict[str, str] | None = None,
        on_click: dict[int, ClickHandler[Self]] | None = None,
    ) -> None:
        """
        Intialize a new status bar content producer.

        The `instance` argument will be provided by swaystatus when the element
        is loaded. This should not be provided by the subclass.

        The dictionary `env` will be added to the execution environment of any
        click handler. Upon instantiation, the value is a combination of the
        values in configuration for `env`, `settings.<name>.env`, and
        `settings."<name>:<instance>".env`, merged together in that order, with
        later values overriding earlier ones. Additionally, the attributes
        `name` and `instance` (if set) are added.

        The dictionary `on_click` maps pointer button numbers to click handlers
        (i.e. functions or shell commands) which take precedence over any
        already defined on the class.

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
            >>>         yield self.block(strftime(self.full_text))

        Without any further changes, it will behave as it did originally, but
        now it can be configured by adding something like the following to the
        configuration file:

            [settings.clock]
            full_text = "The time here is: %r"

        If there are other instances of the module, they will inherit the
        settings, but they can be overridden:

            [settings."clock:home"]
            full_text = "The time at home is: %r"

            [settings."clock:home".env]
            TZ = 'Asia/Tokyo'
        """
        self.instance = instance
        self.env = env or {}
        if on_click:
            for button, handler in on_click.items():
                self.set_on_click_handler(button, handler)

    def __str__(self) -> str:
        return f"element key={self.key!r}"

    @property
    def key(self) -> str:
        return f"{self.name}:{self.instance}" if self.instance else self.name

    def blocks(self) -> Iterator[Block]:
        """
        Yield blocks of content to display on the status bar.

        To create a block, it's recommended to use the `block` method so that
        the block has the proper name and instance set and that there is some
        text:

            >>> from typing import Iterator
            >>> from swaystatus import BaseElement, Block
            >>> class Element(BaseElement):
            >>>     def blocks(self) -> Iterator[Block]:
            >>>         yield self.block("Howdy!")

        There's nothing wrong with creating instances of `Block` directly, but
        it's easier to break the ability for swaystatus to send the element
        click events.

        See the documentation for `block` for a more detailed explanation.
        """
        raise NotImplementedError

    def block(self, full_text: str, **kwargs) -> Block:
        """
        Create a block of content associated with this element.

        This helper ensures that the block it creates is linked to the element
        yielding it, i.e. the name and instance attributes are set correctly,
        which allows click events to be sent to this element.

        Another potential issue happens when a module instance has been
        declared in the configuration `order` with the "name:instance" form and
        the module's element class is also yielding blocks with dynamic
        instance attributes. When swaybar sends click events from these blocks,
        swaystatus is unable to find any known module instances that match and
        falls back to sending it to the "name" module, which may or may not
        exist, and is definitely not the sender.

        To illustrate the problem, consider an element that yields blocks that
        could be different at every update. For example, there could be a
        module that shows network interfaces:

            >>> from pathlib import Path
            >>> from typing import Iterator
            >>> from swaystatus import BaseElement, Block
            >>> class Element(BaseElement):
            >>>     def blocks(self) -> Iterator[Block]:
            >>>         for dev in Path('/sys/class/net').iterdir():
            >>>             yield self.block(dev.name, instance=dev.name)

        The difference between this and the clock example is that the clock
        instances are not dynamic. Swaystatus knows there will always be two
        instances and knows how to reach them.

        The network interfaces example's instances are dynamic, therefore
        swaystatus can only reach this element by the module name.

        The consequence is that a module's instances can either be declared
        statically in the configuration or the blocks created with instances at
        runtime, but not both. Trying to yield a block from the element in
        module "foo" with its instance set to "a" when the module was already
        declared in the configuration `order` as "foo:b" will mean that click
        events will be lost, or worse, sent to the wrong element.

        Using the `block` method will ensure that the returned `Block` has the
        name and instance set correctly. If the block's instance is set
        dynamically and the module's instance was declared in the
        configuration, an exception will be raised.

        See the documentation for `swaystatus.block` for a full specification
        of `Block`'s available fields which can be passed as keyword arguments
        to this method.
        """
        if self.instance is not None:
            kwargs["instance"] = self.instance
        return Block(name=self.name, full_text=full_text, **kwargs)

    def on_click(self, event: ClickEvent) -> None:
        """Perform some action when a status bar block is clicked."""
        try:
            getattr(self, f"on_click_{event.button}")(event)
        except AttributeError:
            pass

    def set_on_click_handler(self, button: int, handler: ClickHandler[Self]) -> None:
        """
        Adds a method to this instance that calls `handler` when blocks from
        this element are clicked with the pointer `button`.

        The `handler` can be one of the following:

            - A function that accepts two positional arguments, this element
              instance and a `ClickEvent`.

            - A shell command compatible with `subprocess.run`, i.e. a string
              or list of strings. Output will be logged at the `DEBUG` level.
              During execution of the handler, all attributes of the event will
              be added to the environment.
        """
        method_name = f"on_click_{button}"
        handler_kind = "function" if callable(handler) else "shell command"
        handler_desc = f"{self} {method_name} {handler_kind}"

        if callable(handler):
            handler_wrapped = handler
        else:

            def prefixed(func: Callable[[str], None]) -> Callable[[str], None]:
                return lambda line: func(f"Output from {handler_desc}: {line.strip()}")

            def handler_wrapped(element: Self, event: ClickEvent):
                PopenStreamHandler(
                    prefixed(logger.debug),
                    prefixed(logger.error),
                    handler,
                    shell=True,
                    text=True,
                ).wait()

        def method_wrapped(self: Self, event: ClickEvent):
            logger.debug(f"Executing {handler_desc} => {handler}")
            environ_save = os.environ.copy()
            os.environ.update(self.env.copy() | {k: str(v) for k, v in event.dict().items()})
            try:
                handler_wrapped(self, event)
            except Exception:
                logger.exception(f"Unhandled exception in {handler_desc}")
            finally:
                os.environ.clear()
                os.environ.update(environ_save)

        logger.info(f"Setting {handler_desc} => {handler}")
        setattr(self, method_name, MethodType(method_wrapped, self))


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


class PopenStreamHandler(Popen):
    """Just like `Popen`, but handle stdout and stderr output in dedicated threads."""

    def __init__(self, stdout_handler, stderr_handler, *args, **kwargs) -> None:
        kwargs["stdout"] = kwargs["stderr"] = PIPE
        super().__init__(*args, **kwargs)
        assert self.stdout and self.stderr
        ProxyThread(self.stdout, stdout_handler).start()
        ProxyThread(self.stderr, stderr_handler).start()


__all__ = [BaseElement.__name__]
