import time
from functools import cached_property
from json import JSONEncoder
from signal import SIGCONT, SIGSTOP
from typing import IO, Any, Iterable, Iterator, Sequence

from .block import Block
from .logging import logger
from .status_line import StatusLine
from .threading import Ticker
from .typing import Seconds


class Timer:
    """Context manager to time the execution of the body."""

    def __enter__(self):
        self.start = time.perf_counter()
        self.seconds = None
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.seconds = time.perf_counter() - self.start


class OutputDriver(Ticker):
    """Steadily drive status line generation."""

    def __init__(self, iterable: Iterable[Sequence[Block]], interval: Seconds) -> None:
        super().__init__(interval=interval, name="output")
        self._iterator = iter(iterable)

    def tick(self) -> None:
        try:
            logger.debug(next(self._iterator))
        except StopIteration:
            pass


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

    def __iter__(self) -> Iterator[Sequence[Block]]:
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
            logger.debug("generated status line in %0.2f seconds", timer.seconds)
            send(",{}".format(encoder.encode(status_line)))
            yield status_line


class Encoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Block):
            return obj.as_dict()
        return super().default(obj)
