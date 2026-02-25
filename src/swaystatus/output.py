"""Output is described in the HEADER and BODY sections of swaybar-protocol(7)."""

import sys
import time
from collections.abc import Iterable, Iterator, Sequence
from functools import cached_property
from json import JSONEncoder
from signal import SIGCONT, SIGSTOP
from typing import Any

from .block import Block
from .element import BaseElement
from .logger import logger
from .threads import Ticker

type Seconds = float | int


class OutputProcessor:
    """Iterate status lines sent to stdout."""

    def __init__(self, elements: Sequence[BaseElement], click_events: bool) -> None:
        self._elements = elements
        self._click_events = click_events

    @cached_property
    def header(self) -> dict[str, Any]:
        return {
            "version": 1,
            "stop_signal": SIGSTOP,
            "cont_signal": SIGCONT,
            "click_events": self._click_events,
        }

    def status_line(self) -> Sequence[Block]:
        return [b for e in self._elements for b in e.blocks()]

    def __iter__(self) -> Iterator[Sequence[Block]]:
        def send(line: str) -> None:
            print(line, file=sys.stdout, flush=True)

        timer = Timer()
        encoder = OutputEncoder()
        send(encoder.encode(self.header))
        send("[[]")
        while True:
            with timer:
                blocks = list(self.status_line())
            send(f",{encoder.encode(blocks)}")
            logger.info("generated status line in %f seconds", timer.seconds)
            logger.debug("status line %r", blocks)
            yield blocks


class OutputDriver(Ticker):
    """Steadily drive status line generation."""

    def __init__(self, iterable: Iterable[Sequence[Block]], interval: Seconds | None) -> None:
        super().__init__(interval=interval, name="OutputThread")
        self._iterator = iter(iterable)

    def tick(self) -> None:
        logger.debug("processed %d output block(s)", len(next(self._iterator)))


class OutputEncoder(JSONEncoder):
    """Serialize a block as a compact JSON-encoded dictionary."""

    def default(self, o):
        return o.min_dict()


class Timer:
    """Context manager to time the execution of the body."""

    def __enter__(self):
        self.start = time.perf_counter()
        self.seconds = None
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.seconds = time.perf_counter() - self.start


__all__ = [
    OutputProcessor.__name__,
    OutputDriver.__name__,
]
