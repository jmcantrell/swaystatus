import json
from functools import cached_property
from typing import IO, Iterable, Iterator

from .click_event import ClickEvent
from .element import BaseElement
from .logging import logger

type Key = tuple[str, str | None]


class InputDelegator:
    """Handle click events, sending them to the appropriate element's handler."""

    def __init__(self, elements: Iterable[BaseElement]) -> None:
        self.elements = list(elements)

    @cached_property
    def elements_by_key(self) -> dict[Key, BaseElement]:
        return {(e.name, e.instance): e for e in self.elements}

    def element_for_event(self, event: ClickEvent) -> BaseElement | None:
        if not event.name:
            return None
        try:
            return self.elements_by_key[(event.name, event.instance)]
        except KeyError:
            pass
        try:
            return self.elements_by_key[(event.name, None)]
        except KeyError:
            pass
        return None

    def process(self, file: IO[str]) -> Iterator[ClickEvent]:
        assert file.readline().strip() == "["
        for line in file:
            try:
                event = ClickEvent(**json.loads(line.strip().lstrip(",")))
            except Exception:
                logger.exception("Exception while decoding input: {line!r}")
                continue
            logger.debug(f"Received click event: {event!r}")
            if element := self.element_for_event(event):
                logger.info(f"Sending {event} to {element}")
                element.on_click(event)
                yield event
            else:
                logger.warning(f"Unable to identify source element for {event}")
