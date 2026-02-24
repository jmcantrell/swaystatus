from functools import cache, cached_property
from json import JSONDecoder
from typing import IO, Iterable, Iterator

from .click_event import ClickEvent
from .element import BaseElement, ClickHandlerResult
from .logging import logger


class InputProcessor:
    """Handle click events, sending them to the appropriate element's handler."""

    def __init__(self, elements: Iterable[BaseElement]) -> None:
        self.elements = list(elements)

    @cached_property
    def elements_by_key(self) -> dict[tuple[str | None, str | None], BaseElement]:
        """Provide fast lookup of elements by name and instance."""
        return {(e.name, e.instance): e for e in self.elements}

    @cache
    def element(self, name: str | None, instance: str | None) -> BaseElement:
        """
        Return the handler for element identifiers.

        Try to find an element matching the given name and instance.
        If a matching element is not found, look for one with the same name.
        Otherwise, raise `KeyError`.
        """
        for instance in (instance, None):
            try:
                return self.elements_by_key[(name, instance)]
            except KeyError:
                pass
        raise KeyError((name, instance))

    def process(self, file: IO[str]) -> Iterator[tuple[ClickEvent, BaseElement, ClickHandlerResult]]:
        """Yield click events and their corresponding element handler results."""
        for click_event in click_events(file):
            logger.debug(f"received click event: {click_event!r}")
            try:
                element = self.element(click_event.name, click_event.instance)
            except KeyError:
                logger.warn(f"no element to handle {click_event}")
                continue
            logger.info(f"sending {click_event} to {element}")
            handler_result = element.on_click(click_event)
            logger.debug(f"{element} handled {click_event} with result: {handler_result!r}")
            yield click_event, element, handler_result


def click_events(file: IO[str]) -> Iterator[ClickEvent]:
    """Yield decoded click events from a file."""
    decoder = Decoder()
    assert file.readline().strip() == "["
    for line in file:
        try:
            yield decoder.decode(line.strip().lstrip(","))
        except Exception:
            logger.exception(f"exception while decoding input: {line!r}")


class Decoder(JSONDecoder):
    def __init__(self) -> None:
        super().__init__(object_hook=lambda kwargs: ClickEvent(**kwargs))


__all__ = [InputProcessor.__name__]
