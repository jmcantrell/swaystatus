from threading import Event, Thread
from typing import Any, Callable


class Ticker(Thread):
    """Run a function at a regular interval or manually."""

    def __init__(
        self,
        tick: Callable[..., Any] | None = None,
        /,
        *,
        interval: float | int | None = None,
        name: str | None = None,
        daemon: bool | None = None,
    ) -> None:
        super().__init__(name=name, daemon=daemon)
        self.interval = interval
        self._tick = tick
        self._next = Event()
        self._done = Event()

    def tick(self) -> None:
        if self._tick:
            self._tick()

    def next(self) -> None:
        self._next.set()

    def run(self) -> None:
        while not self._done.is_set():
            self._next.wait(timeout=self.interval)
            self._next.clear()
            if self._done.is_set():
                break
            self.tick()

    def stop(self) -> None:
        self._done.set()
        self._next.set()
