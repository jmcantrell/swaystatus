from functools import cached_property
from json import JSONDecoder
from typing import IO, Iterable, Iterator

from .click_event import ClickEvent
from .element import BaseElement, ClickHandlerResult
from .logging import logger


class InputDelegator:
    """Handle click events, sending them to the appropriate element's handler."""

    def __init__(self, elements: Iterable[BaseElement]) -> None:
        self.elements = list(elements)

    @cached_property
    def elements_by_key(self) -> dict[tuple[str, str | None], BaseElement]:
        return {(e.name, e.instance): e for e in self.elements}

    def element_for_event(self, event: ClickEvent) -> BaseElement | None:
        if not event.name:
            return None
        for instance in (event.instance, None):
            try:
                return self.elements_by_key[(event.name, instance)]
            except KeyError:
                pass
        return None

    def process(self, file: IO[str]) -> Iterator[tuple[ClickEvent, ClickHandlerResult]]:
        decoder = Decoder()
        assert file.readline().strip() == "["
        for line in file:
            try:
                event = decoder.decode(line.strip().lstrip(","))
            except Exception:
                logger.exception("exception while decoding input: {line!r}")
                continue
            logger.debug(f"received click event: {event!r}")
            if element := self.element_for_event(event):
                logger.info(f"sending {event} to {element}")
                yield event, element.on_click(event)
            else:
                logger.warning(f"unable to identify source element for {event}")


class Decoder(JSONDecoder):
    def __init__(self) -> None:
        super().__init__(object_hook=lambda kwargs: ClickEvent(**kwargs))


__all__ = [InputDelegator.__name__]
