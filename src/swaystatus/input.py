"""Input is described in the CLICK EVENTS section of swaybar-protocol(7)."""

import sys
from collections.abc import Callable, Iterable, Iterator, Sequence
from contextvars import copy_context
from functools import cached_property
from json import JSONDecoder
from threading import Thread
from typing import Any

from .click_event import ClickEvent
from .context import context_group
from .element import BaseElement, UpdateHandler
from .logger import logger

type Callback = Callable[..., Any]
type ElementKey = tuple[str, str | None]


class InputProcessor:
    """Iterate handled click events received from stdin."""

    def __init__(self, elements: Sequence[BaseElement], updater: Callback) -> None:
        self._elements = elements
        self._updater = updater

    @cached_property
    def _element_lookup(self) -> dict[ElementKey, BaseElement]:
        return {(e.name, e.instance): e for e in self._elements}

    def click_target(self, name: str, instance: str | None = None) -> BaseElement:
        try:
            return self._element_lookup[(name, instance)]
        except KeyError:
            return self._element_lookup[(name, None)]

    def update(self) -> None:
        logger.info("updating")
        self._updater()

    def __iter__(self) -> Iterator[ClickEvent]:
        decoder = InputDecoder()
        lines = iter(sys.stdin)
        assert next(lines).strip() == "["
        for line in lines:
            with context_group("click event"):
                click_event = decoder.decode(line.strip().lstrip(","))
                logger.info("received %s", click_event)
                logger.debug("%r", click_event)
                if not click_event.name:
                    logger.warning("click event missing element name")
                    continue
                try:
                    element = self.click_target(click_event.name, click_event.instance)
                except KeyError:
                    logger.warning("target element not found")
                    continue
                logger.info("sending to %s", element)
                update_request = element.on_click(click_event)
                if callable(update_request):
                    UpdateDriver(update_request, self.update).start()
                elif update_request:
                    self.update()
                yield click_event


class InputDriver(Thread):
    """Eagerly drive click event processing."""

    def __init__(self, iterable: Iterable[ClickEvent]) -> None:
        super().__init__(name="InputThread", daemon=True)
        self._iterator = iter(iterable)

    def run(self) -> None:
        for click_event in self._iterator:
            logger.debug("processed input %s", click_event)


class InputDecoder(JSONDecoder):
    """Deserialize a click event object from a JSON-encoded dictionary."""

    def __init__(self) -> None:
        super().__init__(object_hook=lambda kwargs: ClickEvent(**kwargs))


class UpdateDriver(Thread):
    """Handle an update request concurrently with processing."""

    def __init__(self, update_handler: UpdateHandler, updater: Callback) -> None:
        super().__init__(name="UpdateThread", daemon=True, context=copy_context())
        self._update_handler = update_handler
        self._updater = updater

    def run(self) -> None:
        if self._update_handler():
            self._updater()


__all__ = [
    InputProcessor.__name__,
    InputDriver.__name__,
]
