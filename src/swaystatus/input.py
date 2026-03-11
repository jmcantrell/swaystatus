from json import JSONDecoder
from threading import Thread
from typing import IO, Any, Callable, Iterable, Iterator

from .click_event import ClickEvent
from .logging import logger
from .status_line import StatusLine

type InputProcessed = ClickEvent


class InputProcessor:
    """Handle click events, sending them to the appropriate element's handler."""

    def __init__(
        self,
        file: IO[str],
        status_line: StatusLine,
        updater: Callable[..., Any],
    ) -> None:
        self._file = file
        self._status_line = status_line
        self._updater = updater

    def __iter__(self) -> Iterator[InputProcessed]:
        """Yield click events and their corresponding element handler results."""
        decoder = Decoder()
        assert self._file.readline().strip() == "["
        for line in self._file:
            click_event = decoder.decode(line.strip().lstrip(","))
            logger.debug("received click event: %r", click_event)
            if not click_event.name:
                logger.warning("unidentified %s", click_event)
                continue
            try:
                element = self._status_line.click_target(click_event.name, click_event.instance)
            except KeyError:
                logger.warning("no element to handle %s", click_event)
                continue
            logger.info("sending %s to %s", click_event, element)
            if update := element.on_click(click_event):
                self._updater()
            logger.debug("%s handled %s with update=%s", element, click_event, update)
            yield click_event


class InputDriver(Thread):
    """Eagerly drive click event processing and handle updates."""

    def __init__(self, iterable: Iterable[InputProcessed]) -> None:
        super().__init__(name="input", daemon=True)
        self._iterator = iter(iterable)

    def run(self) -> None:
        for item in self._iterator:
            logger.debug("processed input: %r", item)


class Decoder(JSONDecoder):
    def __init__(self) -> None:
        super().__init__(object_hook=lambda kwargs: ClickEvent(**kwargs))


__all__ = [
    InputProcessor.__name__,
    InputDriver.__name__,
]
