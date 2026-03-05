"""
An element produces blocks of content to display in the status bar.

When the status bar is running, every configured element will be prompted for
blocks at the configured interval. Once every element has replied, all of the
collected blocks are encoded and sent to the bar via stdout.
"""

from functools import cache, cached_property
from subprocess import Popen
from types import MethodType
from typing import Callable, Iterable, Iterator, Mapping, Self, Sequence

from .block import Block
from .click_event import ClickEvent
from .env import environ_update
from .logging import logger
from .subprocess import ShellCommandProcess

type UpdateHandler = Callable[[], bool]
type ShellCommand = str | Sequence[str]
type ClickHandlerResult = ShellCommand | Popen | UpdateHandler | bool | None
type ClickHandler[E] = Callable[[E, ClickEvent], ClickHandlerResult]


class BaseElement:
    """
    Base class for constructing elements for the status bar.

    The subclass must be named `Element` and be contained in a module file
    whose name will be used by swaystatus to identify it. For example, if there
    is a module file named `clock.py`, the class will have an attribute `name`
    set to "clock".

    The `blocks` method is called to generate output at every interval and must
    be overridden. There is no requirement regarding the number of blocks that
    are yielded, however if no blocks are yielded, nothing will be visible in
    the status bar for that element. This may be desirable if, for example, the
    element yields a block for every mounted disk and there are none mounted.

    A hypothetical clock module file might contain the following:

        >>> from time import strftime
        >>> from typing import Iterator
        >>> from swaystatus import BaseElement, Block
        >>> class Element(BaseElement):
        >>>     def blocks(self) -> Iterator[Block]:
        >>>         yield self.block(strftime("%c"))

    Enable the element by adding it to the configuration file:

        order = ["clock"]

    Let's make the clock respond to a left mouse button click by running a
    shell command. Enable click events and add a click handler to the settings
    for that element:

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
    element, each having their own settings.

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
        >>> element = Element(instance="home")

    You should not set these attributes yourself, as it will confuse and sadden
    swaystatus, and it will propably not respond to your clicks.
    """

    name: str
    instance: str | None
    env: dict[str, str]

    def __init__(
        self,
        *,
        instance: str | None = None,
        env: Mapping[str, str] | None = None,
        on_click: Mapping[int, ShellCommand | ClickHandler[Self]] | None = None,
    ) -> None:
        """
        Intialize a new status bar content producer, i.e. an element.

        The `instance` argument will be provided by swaystatus when the element
        is created. This should not be provided by the subclass.

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
        configuration of how the element displays the time. Add an initializer
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

        If there are other instances of the element, they will inherit the
        settings, but they can be overridden:

            [settings."clock:home"]
            full_text = "The time at home is: %r"

            [settings."clock:home".env]
            TZ = 'Asia/Tokyo'
        """
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

        To create a block, it's recommended to use the `block` method so that
        the block has the proper name and instance set and that there is some
        text:

            >>> from typing import Iterator
            >>> from swaystatus import BaseElement, Block
            >>> class Element(BaseElement):
            >>>     def blocks(self) -> Iterator[Block]:
            >>>         yield self.block("Howdy!")

        See the documentation for `block` for a more detailed explanation.
        """
        raise NotImplementedError

    def block(self, full_text, instance: str | None = None) -> Block:
        """
        Create a block of content associated with this element.

        This method ensures that the `Block` it creates is linked to the
        element yielding it, i.e. the name and instance attributes are set
        correctly, which allows click events to be sent to this element.

        One potential issue happens when an element instance has been declared
        in the configuration `order` with the "name:instance" form and the
        element class is also yielding blocks with dynamic instance attributes.
        When swaybar sends click events from these blocks, swaystatus is unable
        to match it with any of the elements it knows about and falls back to
        sending it to the "name" element, which may or may not exist, and is
        definitely not the sender.

        To illustrate the problem, consider an element that yields blocks that
        could be different at every update. For example, there could be an
        element that shows network interfaces:

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

        The blocks coming from this new example have potentially different
        instances at every update, so swaystatus can only reach this element by
        the module name.

        The consequence is that an element's instances can either be declared
        statically in the configuration or the blocks created with instances at
        runtime, but not both. Trying to yield a block from the element "foo"
        with its instance set to "a" when the element was already declared in
        the configuration `order` as "foo:b" will mean that click events will
        be lost, or worse, sent to the wrong element.

        Using the `block` method will ensure that the returned `Block` has the
        name and instance set correctly. If the block's instance is set
        dynamically and the element's instance was declared in the
        configuration, an exception will be raised.
        """
        if instance and self.instance:
            raise ValueError("block instance is not allowed when element instance is already set")
        return Block(name=self.name, instance=instance or self.instance, full_text=full_text)

    def set_click_handler(self, button: int, handler: ShellCommand | ClickHandler[Self]) -> None:
        """
        Add a method to this instance that calls `handler` when blocks from
        this element are clicked with the pointer `button`.

        During execution of the handler, additions from any `env` configuration
        and all attributes of the event will be added to the execution
        environment.

        The `handler` can be one of the following:

            - A shell command compatible with `Popen`, i.e. a string or list of
              strings. The stdout and stderr streams will be logged at the
              `DEBUG` and `ERROR` levels, respectively. It will be allowed to
              finish in a separate thread, and if the return code is zero, the
              status bar will be updated.

            - A function that accepts two positional arguments (this element
              instance and a `ClickEvent`) and returns one of the following:

                  - A shell command. It will be handled like the first item.

                  - A `Popen` object. It will be allowed to finish in a
                    separate thread, and if the return code is zero, the status
                    bar will be updated.

                  - A function that returns a `bool`. It will be run in a
                    separate thread, and if it returns `True`, the status bar
                    will be updated.

                  - A `bool`. If `True`, the status bar will be updated.

                  - Nothing or `None`. The status bar will not be updated.
        """

        if not callable(handler):

            def handler_wrapped(element: Self, click_event: ClickEvent) -> ClickHandlerResult:
                return handler

            self.set_click_handler(button, handler_wrapped)
            return

        logger.debug("setting %s handler: %r", self, handler)
        setattr(self, f"on_click_{button}", MethodType(handler, self))

    def on_click(self, click_event: ClickEvent) -> UpdateHandler | bool:
        """Delegate a click event to the handler corresponding to its button."""
        try:
            click_handler = getattr(self, f"on_click_{click_event.button}")
        except AttributeError:
            return False

        logger.debug("executing click handler: %r", click_handler)

        with environ_update(**self.env | click_event.as_dict()):
            result = click_handler(click_event)

            if result is None:
                return False

            if isinstance(result, bool):
                return result

            if isinstance(result, str | list):
                logger.debug("executing shell command=%r", result)
                result = ShellCommandProcess(result)

            if isinstance(result, Popen):

                def update_handler() -> bool:
                    result.communicate()
                    return result.returncode == 0

                return update_handler

            return result


class ElementRegistry:
    """Locate an element instance in order of specificity."""

    def __init__(self, elements: Iterable[BaseElement]) -> None:
        self.elements = elements

    @cached_property
    def elements_by_key(self) -> Mapping[tuple[str, str | None], BaseElement]:
        return {(e.name, e.instance): e for e in self.elements}

    @cache
    def get(self, name: str, instance: str | None = None) -> BaseElement:
        """
        Return the element identified by a name and optional instance.

        If a matching element is not found, look for one with the same name.
        Otherwise, raise `KeyError`.
        """
        if instance:
            try:
                return self.elements_by_key[(name, instance)]
            except KeyError:
                pass
        return self.elements_by_key[(name, None)]


__all__ = [
    BaseElement.__name__,
    ElementRegistry.__name__,
]
