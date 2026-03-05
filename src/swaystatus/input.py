from json import JSONDecoder
from typing import IO, Iterable, Iterator

from .click_event import ClickEvent
from .element import BaseElement, ElementRegistry, UpdateHandler
from .logging import logger


class InputProcessor:
    """Handle click events, sending them to the appropriate element's handler."""

    def __init__(self, elements: Iterable[BaseElement]) -> None:
        self.elements = ElementRegistry(elements)

    def process(self, file: IO[str]) -> Iterator[UpdateHandler | bool]:
        """Yield click events and their corresponding element handler results."""
        for click_event in parse_click_events(file):
            logger.debug("received click event: %r", click_event)
            if not click_event.name:
                logger.info("ignoring unidentified %s", click_event)
                continue
            try:
                element = self.elements.get(click_event.name, click_event.instance)
            except KeyError:
                logger.warn("no element to handle %s", click_event)
                continue
            logger.info("sending %s to %s", click_event, element)
            update = element.on_click(click_event)
            logger.debug("%s handled %s: %r", element, click_event, update)
            yield update


def parse_click_events(file: IO[str]) -> Iterator[ClickEvent]:
    """Yield parsed click events from a file."""
    decoder = Decoder()
    assert file.readline().strip() == "["
    for line in file:
        yield decoder.decode(line.strip().lstrip(","))


class Decoder(JSONDecoder):
    def __init__(self) -> None:
        super().__init__(object_hook=lambda kwargs: ClickEvent(**kwargs))


__all__ = [InputProcessor.__name__]
