import time
from functools import cached_property
from json import JSONEncoder
from signal import SIGCONT, SIGSTOP
from typing import IO, Any, Iterable, Iterator, Sequence

from .block import Block
from .logging import logger
from .status_line import StatusLine
from .threading import Ticker

type OutputProcessed = Sequence[Block]


class OutputProcessor:
    """Encode status line iterations and send them to an output file."""

    def __init__(self, file: IO[str], status_line: StatusLine, click_events: bool) -> None:
        self._file = file
        self._status_lines = iter(status_line)
        self._click_events = bool(click_events)

    @cached_property
    def header(self) -> dict[str, Any]:
        return dict(
            version=1,
            stop_signal=SIGSTOP,
            cont_signal=SIGCONT,
            click_events=self._click_events,
        )

    def __iter__(self) -> Iterator[OutputProcessed]:
        """Send encoded status lines to output and yield the contained blocks."""

        def send(line: str) -> None:
            print(line, file=self._file, flush=True)

        encoder = Encoder()
        timer = Timer()
        send(encoder.encode(self.header))
        send("[[]")
        while True:
            with timer:
                status_line = next(self._status_lines)
            logger.info("generated status line in %0.2f seconds", timer.seconds)
            send(",{}".format(encoder.encode(status_line)))
            yield status_line


class OutputDriver(Ticker):
    """Steadily drive status line generation."""

    def __init__(
        self,
        iterable: Iterable[OutputProcessed],
        interval: float | int | None,
    ) -> None:
        super().__init__(interval=interval, name="output")
        self._iterator = iter(iterable)

    def tick(self) -> None:
        logger.debug("processed output: %r", next(self._iterator))


class Timer:
    """Context manager to time the execution of the body."""

    def __enter__(self):
        self.start = time.perf_counter()
        self.seconds = None
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.seconds = time.perf_counter() - self.start


class Encoder(JSONEncoder):
    def default(self, block: Block):
        return block.as_dict()


__all__ = [
    OutputProcessor.__name__,
    OutputDriver.__name__,
]
