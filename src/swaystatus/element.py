"""An element produces blocks of content to display in the status bar."""

from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from contextvars import copy_context
from dataclasses import asdict
from subprocess import PIPE, Popen
from threading import Thread
from types import MethodType
from typing import Self

from .block import Block
from .click_event import ClickEvent
from .env import environ_update
from .logger import logger

type EnvMapping = Mapping[str, str | None]
type ShellCommand = str | Sequence[str]
type UpdateHandler = Callable[..., bool]
type UpdateRequest = UpdateHandler | bool
type ClickHandlerResult = ShellCommand | Popen | UpdateRequest | None
type ClickHandler[Element] = Callable[[Element, ClickEvent], ClickHandlerResult]
type ClickHandlerMapping[Element] = Mapping[int, ShellCommand | ClickHandler[Element] | None]


class BaseElement:
    """
    Base class for constructing content-producing elements for the status bar.

    The subclass must be named `Element` and be contained in a module file
    whose name will be used by swaystatus to identify it. For example, if there
    is a module file named `clock.py`, the instantiated element will have its
    attribute `name` set to "clock".

    The `blocks` method must be implemented. It is called to generate output
    every time the status line updates. There is no requirement regarding the
    number of blocks that are yielded, however if no blocks are yielded,
    nothing will be visible in the status bar for that element. This may be
    desirable if, for example, the element yields a block for every mounted
    disk and there are none mounted.

    A minimal clock module file might contain the following:

        >>> from time import strftime
        >>> from collections.abc import Iterator
        >>> from swaystatus import BaseElement, Block
        >>> class Element(BaseElement):
        >>>     def blocks(self) -> Iterator[Block]:
        >>>         yield self.block(strftime("%c"))

    To use this module, it needs to be added to the configuration:

        [[modules]]
        name = "clock"

    This assumes that the module file `clock.py` is in a directory where
    swaystatus can find it (see documentation for `swaystatus.modules`).
    """

    def __init__(
        self,
        name: str,
        instance: str | None = None,
        env: EnvMapping | None = None,
        on_click: ClickHandlerMapping[Self] | None = None,
    ) -> None:
        """
        Intialize a new status bar content producer, i.e. an element.

        All arguments required by the base class, i.e. the arguments listed
        above, will be provided by swaystatus when the element is created.

        The `name` parameter will be the name (minus extension) of the module
        file that the subclass is loaded from.

        The optional `instance` parameter will be provided if the corresponding
        module declaration in the configuration sets it.

        The mapping `env` will be merged into the execution environment of
        any click handler during its execution.

        The mapping `on_click` maps pointer button numbers to click handlers
        (i.e. functions or shell commands) which take precedence over any
        already defined on the class.

        Any extra parameters from the `params` mapping in the configuration
        will be passed as keyword arguments to the element subclass and should
        be handled there.

        Upon instantiation, the mapping parameters `env` and `on_click`, and
        the keyword arguments taken from `params` represent a combination of
        the corresponding tables in the configuration, merged together in order
        of specificity with more specific tables overriding less specific ones.

        To illustrate, let's change the clock example from earlier to allow
        configuring how the element displays the time. Add an initializer that
        accepts and forwards all arguments, handle a new parameter `text` that
        will provide a format string, and change the `blocks` method to use the
        setting:

            >>> from time import strftime
            >>> from collections.abc import Iterator
            >>> from swaystatus import BaseElement, Block
            >>> class Element(BaseElement):
            >>>     def __init__(self, *args, text="%c", **kwargs) -> None:
            >>>         super().__init__(*args, **kwargs)
            >>>         self.text = text
            >>>     def blocks(self) -> Iterator[Block]:
            >>>         yield self.block(strftime(self.text))

        Without any further changes, it will behave as it did originally, but
        now it can be configured by adding an entry to the "clock" module's
        `params` table in the configuration file:

            [[modules]]
            name = "clock"
            [modules.settings]
            params = { text = "epoch seconds %s" }

        See the `swaystatus.config` documentation for more details on
        configuring module parameters.
        """
        self.name = name
        self.instance = instance
        self.env = dict(env or {})
        if on_click:
            for button, handler in on_click.items():
                self.set_click_handler(button, handler)

    def __str__(self) -> str:
        return f"element name={self.name!r} instance={self.instance!r}"

    def blocks(self) -> Iterator[Block]:
        """
        Yield blocks of content to display on the status bar.

        To create a block, it's recommended to use the `block` method to ensure
        that the block yielded is associated with the originating element.

            >>> from collections.abc import Iterator
            >>> from swaystatus import BaseElement, Block
            >>> class Element(BaseElement):
            >>>     def blocks(self) -> Iterator[Block]:
            >>>         yield self.block("Howdy!")

        You could, of course, create and yield a similar block without using
        the `block` method, but using it reduces boilerplate and the chance of
        misconfiguration (see `block` documentation for a full explanation).
        """
        raise NotImplementedError

    def block(self, full_text: str) -> Block:
        """
        Return a block of content associated with this element.

        This method ensures that the block it returns is associated with the
        element creating it, i.e. the block has the `name`, `instance`, and
        `full_text` attributes set properly, ensuring visibility and response
        to click events.

        One potential issue happens when a module has been declared in the
        configuration with an `instance` set and the corresponding element is
        also yielding blocks with dynamic instance attributes.

        When swaybar sends click events from these blocks, swaystatus is unable
        to match it with any of the known elements and falls back to sending
        the click event to an element with the same `name` and no instance,
        which may or may not exist, and is definitely not the sender.

        To illustrate the problem, consider an element that yields blocks that
        could be different at every update. For example, there could be an
        element that shows network interfaces:

            >>> from pathlib import Path
            >>> from collections.abc import Iterator
            >>> from swaystatus import BaseElement, Block
            >>> class Element(BaseElement):
            >>>     def blocks(self) -> Iterator[Block]:
            >>>         for dev in Path('/sys/class/net').iterdir():
            >>>             block = self.block(dev.name)
            >>>             block.instance = dev.name
            >>>             yield block

        The difference between this and the clock example is that the clock
        instances are not dynamic. Swaystatus knows how many instances exist
        and how to reach them.

        The blocks coming from this new example have potentially different
        instances at every update, so swaystatus can only reach this element by
        the module name.

        The consequence is that, if click events are required, a module
        `instance` can either be declared statically in the configuration or
        dynamically by the module's element at runtime, but not both.

        For example, trying to yield a block with an `instance` of "work" from
        the element named "clock" when the module was already declared in the
        configuration with the `instance` "home" will mean that click events
        will be lost, or worse, sent to the wrong element for handling.
        """
        return Block(name=self.name, instance=self.instance, full_text=full_text)

    def set_click_handler(self, button: int, click_handler: ClickHandler[Self] | ShellCommand | None) -> None:
        """
        Specify how clicks events sent to this element for `button` should be handled.

        The `click_handler` can be one of the following:

            - A function that accepts two positional arguments (this element
              instance and a ClickEvent) and returns one of the following:

                - A shell command compatible with Popen. The stdout and stderr
                  streams will be logged at the DEBUG and ERROR levels,
                  respectively. If the exit status is zero, the status bar will
                  be updated.

                - A Popen object. If the exit status is zero, the status bar
                  will be updated.

                - A function that returns a bool. If it returns True, the
                  status bar will be updated.

                - A bool. If True, the status bar will be updated.

                - Nothing or None. The status bar will not be updated.

            - A shell command. It will be handled as described above.

            - None. Clicks events will not be handled for `button`. This will
              override any methods defined in the element subclass.
        """

        method: ClickHandler[Self]
        method_attr = f"on_click_{button}"

        if click_handler is None:

            def method(*args, **kwargs) -> None:
                pass

        elif not callable(click_handler):

            def method(*args, **kwargs) -> ShellCommand:
                return click_handler

        else:
            method = click_handler

        setattr(self, method_attr, MethodType(method, self))

    def on_click(self, click_event: ClickEvent) -> UpdateRequest:
        """Delegate a click event to the handler corresponding to its button."""
        method_attr = f"on_click_{click_event.button}"

        try:
            handler = getattr(self, method_attr)
            logger.debug("click handler method %r", handler)
        except AttributeError:
            return False

        env = self.env | asdict(click_event)
        logger.debug("click handler environment %r", env)

        with environ_update(**env):
            result: ClickHandlerResult = handler(click_event)
            logger.debug("click handler result %r", result)

            if result is None:
                return False

            if isinstance(result, bool) or callable(result):
                return result

            if isinstance(result, str | Sequence):
                result = LoggedProcess(result)

            def update_request() -> bool:
                result.wait()
                return result.returncode == 0

            return update_request


class LoggedProcess(Popen):
    """Run a shell command, logging stdout and stderr."""

    def __init__(self, args: ShellCommand) -> None:
        super().__init__(args, stdout=PIPE, stderr=PIPE, shell=True, text=True)
        assert self.stdout and self.stderr

        def wrap(log: Callable[[str], None]) -> Callable[[str], None]:
            def wrapped(line: str) -> None:
                log(line.rstrip("\n"))

            return wrapped

        self._stdout_thread = MapDriver(self.stdout, wrap(logger.debug), name=f"LoggerThread.{self.pid}.stdout")
        self._stdout_thread.start()
        self._stderr_thread = MapDriver(self.stderr, wrap(logger.error), name=f"LoggerThread.{self.pid}.stderr")
        self._stderr_thread.start()

    def wait(self, timeout: float | int | None = None) -> int:
        result = super().wait(timeout=timeout)
        self._stdout_thread.join(timeout=timeout)
        self._stderr_thread.join(timeout=timeout)
        assert self.stdout and self.stderr
        self.stdout.close()
        self.stderr.close()
        return result


class MapDriver[T](Thread):
    """Eagerly drive items from an iterable into a function."""

    def __init__(self, iterable: Iterable[T], handler: Callable[[T], None], name: str | None = None) -> None:
        super().__init__(name=name, daemon=True, context=copy_context())
        self._iterator = iter(iterable)
        self._handler = handler

    def run(self) -> None:
        for item in self._iterator:
            self._handler(item)


__all__ = [BaseElement.__name__]
