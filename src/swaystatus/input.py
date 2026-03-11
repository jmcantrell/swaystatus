from json import JSONDecoder
from threading import Thread
from typing import IO, Iterable, Iterator

from .click_event import ClickEvent
from .logging import logger
from .status_line import StatusLine


class InputDriver(Thread):
    """Eagerly drive click event processing and handle updates."""

    def __init__(self, iterable: Iterable[ClickEvent]) -> None:
        super().__init__(name="input", daemon=True)
        self._iterator = iter(iterable)

    def run(self) -> None:
        for item in self._iterator:
            logger.debug(item)


class InputProcessor:
    """Handle click events, sending them to the appropriate element's handler."""

    def __init__(self, file: IO[str], status_line: StatusLine) -> None:
        self._file = file
        self._status_line = status_line

    def __iter__(self) -> Iterator[ClickEvent]:
        """Yield click events and their corresponding element handler results."""
        for click_event in parse_click_events(self._file):
            logger.debug("received click event: %r", click_event)
            if not click_event.name:
                logger.info("ignoring unidentified %s", click_event)
                continue
            try:
                element = self._status_line.click_target(click_event.name, click_event.instance)
            except KeyError:
                logger.warn("no element to handle %s", click_event)
                continue
            logger.info("sending %s to %s", click_event, element)
            update = element.on_click(click_event)
            logger.debug("%s handled %s: %r", element, click_event, update)
            yield click_event


def parse_click_events(file: IO[str]) -> Iterator[ClickEvent]:
    """Yield parsed click events from a file."""
    decoder = Decoder()
    assert file.readline().strip() == "["
    for line in file:
        yield decoder.decode(line.strip().lstrip(","))


class Decoder(JSONDecoder):
    def __init__(self) -> None:
        super().__init__(object_hook=lambda kwargs: ClickEvent(**kwargs))
