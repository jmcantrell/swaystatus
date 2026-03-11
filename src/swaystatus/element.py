from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from subprocess import PIPE, Popen
from threading import Thread
from types import MethodType
from typing import Self

from .block import Block
from .click_event import ClickEvent
from .env import environ_update
from .logging import logger

type EnvMapping = dict[str, str | None]
type ShellCommand = str | Sequence[str]
type UpdateHandler = Callable[[], bool]
type UpdateRequest = UpdateHandler | bool
type ClickHandlerResult = ShellCommand | Popen | UpdateRequest | None
type ClickHandler[E] = Callable[[E, ClickEvent], ClickHandlerResult]
type ClickHandlerMapping[E] = Mapping[int, ShellCommand | ClickHandler[E] | None]


class BaseElement:
    """
    Base class for constructing elements for the status bar.

    The subclass must be named `Element` and be contained in a module file
    whose name will be used by swaystatus to identify it. For example, if there
    is a module file named `clock.py`, the instantiated element will have an
    attribute `name` set to "clock".

    The `blocks` method is required on all subclasses. It is called to generate
    output every time the status line updates. There is no requirement
    regarding the number of blocks that are yielded, however if no blocks are
    yielded, nothing will be visible in the status bar for that element. This
    may be desirable if, for example, the element yields a block for every
    mounted disk and there are none mounted.

    A minimal clock module file might contain the following:

        >>> from time import strftime
        >>> from typing import Iterator
        >>> from swaystatus import BaseElement, Block
        >>> class Element(BaseElement):
        >>>     def blocks(self) -> Iterator[Block]:
        >>>         yield self.block(strftime("%c"))
    """

    def __init__(
        self,
        name: str,
        instance: str | None = None,
        /,
        *,
        env: EnvMapping | None = None,
        on_click: ClickHandlerMapping[Self] | None = None,
    ) -> None:
        """
        Intialize a new status bar content producer, i.e. an element.

        All arguments required by the base class will be provided by swaystatus
        when the element is created.

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

        Upon instantiation, the parameters `env`, `on_click`, and the keyword
        arguments taken from `params` represent a combination of the
        corresponding tables in the configuration, merged together in order of
        specificity with more specific tables overriding less specific ones.

        To illustrate, let's change the clock example from earlier to allow
        configuring how the element displays the time. Add an initializer that
        accepts and forwards all arguments, handle a new parameter `full_text`
        that will provide a format string, and change the `blocks` method to
        use the setting:

            >>> from time import strftime
            >>> from typing import Iterator
            >>> from swaystatus import BaseElement, Block
            >>> class Element(BaseElement):
            >>>     def __init__(self, *args, full_text="%c", **kwargs) -> None:
            >>>         super().__init__(*args, **kwargs)
            >>>         self.full_text = full_text
            >>>     def blocks(self) -> Iterator[Block]:
            >>>         yield self.block(strftime(self.full_text))

        Without any further changes, it will behave as it did originally, but
        now it can be configured for by adding it to a "clock" module's
        `params` table in the configuration file:

            [[modules]]
            name = "clock"
            params = { full_text = "epoch seconds %s" }
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

            >>> from typing import Iterator
            >>> from swaystatus import BaseElement, Block
            >>> class Element(BaseElement):
            >>>     def blocks(self) -> Iterator[Block]:
            >>>         yield self.block("Howdy!")

        See the documentation for `block` for a more detailed explanation.
        """
        raise NotImplementedError

    def block(self, full_text) -> Block:
        """
        Create a block of content associated with this element.

        This method ensures that the block it returns is associated with the
        element creating it, i.e. the block has the `name`, `instance`, and
        `full_text` attributes set properly, ensuring visibility and response
        to click events.

        One potential issue happens when an module has been declared in the
        configuration with an `instance` set and the corresponding element is
        also yielding blocks with dynamic instance attributes.

        When swaybar sends click events from these blocks, swaystatus is unable
        to match it with any of the elements it is aware of and falls back to
        sending it to an element with the same `name`, which may or may not
        exist, and is definitely not the sender.

        To illustrate the problem, consider an element that yields blocks that
        could be different at every update. For example, there could be an
        element that shows network interfaces:

            >>> from pathlib import Path
            >>> from typing import Iterator
            >>> from swaystatus import BaseElement, Block
            >>> class Element(BaseElement):
            >>>     def blocks(self) -> Iterator[Block]:
            >>>         for dev in Path('/sys/class/net').iterdir():
            >>>             block = self.block(dev.name)
            >>>             block.instance = dev.name
            >>>             yield block

        The difference between this and the clock example is that the clock
        instances are not dynamic. Swaystatus knows there is exactly one
        instance and how to reach them.

        The blocks coming from this new example have potentially different
        instances at every update, so swaystatus can only reach this element by
        the module name.

        The consequence is that a module `instance` can either be declared
        statically in the configuration or dynamically by the module's element
        at runtime, but not both.

        For example, trying to yield a block with an `instance` of "work" from
        the element named "clock" when the module was already declared in the
        configuration with the `instance` "home" will mean that click events
        will be lost, or worse, sent to the wrong element.
        """
        return Block(
            name=self.name,
            instance=self.instance,
            full_text=full_text,
        )

    def set_click_handler(
        self,
        button: int,
        click_handler: ClickHandler[Self] | ShellCommand | None,
    ) -> None:
        """
        Specify how clicks events sent to this element for `button` should be
        handled.

        The `click_handler` can be one of the following:

            - A function that accepts two positional arguments (this element
              instance and a ClickEvent) and returns one of the following:

                - A shell command compatible with Popen, i.e. a str|list[str].
                  The stdout and stderr streams will be logged at the DEBUG and
                  ERROR levels, respectively. If the exit status is zero, the
                  status bar will be updated.

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

        method_attr = f"on_click_{button}"

        if click_handler is None:

            def handler_disabled(*args, **kwargs) -> None:
                pass

            self.set_click_handler(button, handler_disabled)
            return

        if not callable(click_handler):

            def handler_wrapped(*args, **kwargs) -> ShellCommand:
                return click_handler

            self.set_click_handler(button, handler_wrapped)
            return

        logger.debug("setting %s click handler for button=%s: %r", self, button)
        setattr(self, method_attr, MethodType(click_handler, self))

    def on_click(self, click_event: ClickEvent) -> bool:
        """Delegate a click event to the handler corresponding to its button."""
        try:
            click_handler = getattr(self, f"on_click_{click_event.button}")
        except AttributeError:
            return False

        logger.debug("executing %s click handler for %s", self, click_event)

        with environ_update(**self.env | click_event.as_dict()):
            result: ClickHandlerResult = click_handler(click_event)

            if result is None:
                return False

            if isinstance(result, bool):
                return result

            if callable(result):
                return result()

            if isinstance(result, str | Sequence):
                logger.debug("executing shell command: %s", result)
                result = LoggedProcess(result)

            result.wait()
            return result.returncode == 0


class MapDriver[T](Thread):
    """Eagerly drive items from an iterable into a function."""

    def __init__(
        self,
        iterable: Iterable[T],
        handler: Callable[[T], None],
        name: str | None = None,
    ) -> None:
        super().__init__(name=name, daemon=True)
        self._iterator = iter(iterable)
        self._handler = handler

    def run(self) -> None:
        for item in self._iterator:
            self._handler(item)


class LoggedProcess(Popen):
    """Run a shell command, logging stdout and stderr."""

    def __init__(self, args: ShellCommand) -> None:
        super().__init__(args, stdout=PIPE, stderr=PIPE, shell=True, text=True)
        assert self.stdout and self.stderr

        def without_newline(func: Callable[[str], None]) -> Callable[[str], None]:
            def wrapped(line: str) -> None:
                func(line.rstrip("\n"))

            return wrapped

        self._stdout_thread = MapDriver(self.stdout, without_newline(logger.debug), name="stdout")
        self._stdout_thread.start()

        self._stderr_thread = MapDriver(self.stderr, without_newline(logger.error), name="stderr")
        self._stderr_thread.start()

    def wait(self, timeout: float | int | None = None):
        result = super().wait(timeout=timeout)
        self._stdout_thread.join(timeout=timeout)
        self._stderr_thread.join(timeout=timeout)
        assert self.stdout and self.stderr
        self.stdout.close()
        self.stderr.close()
        return result


__all__ = [BaseElement.__name__]
