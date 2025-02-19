import json
import locale
import sys
from functools import cached_property
from signal import SIGCONT, SIGINT, SIGSTOP, SIGTERM, SIGUSR1, Signals, signal
from threading import Event, Thread
from typing import Iterable, Iterator

from .element import BaseElement
from .logging import logger
from .updater import Updater

type Seconds = float

header = {
    "version": 1,
    "stop_signal": SIGSTOP,
    "cont_signal": SIGCONT,
    "click_events": False,
}
body_start = "[[]"
body_item = ",{}"


class OutputWriter:
    file = sys.stdout

    def __init__(self, updater: Updater, interval: Seconds, click_events: bool) -> None:
        self.updater = updater
        self.interval = interval
        self.click_events = click_events
        self._tick = Event()
        self._running = Event()

    def send(self, line: str) -> None:
        print(line, flush=True, file=self.file)

    def update(self) -> None:
        self._tick.set()

    def stop(self) -> None:
        self._running.clear()
        self._tick.set()

    def start(self) -> None:
        self.send(json.dumps(header | dict(click_events=self.click_events)))
        self.send(body_start)
        self._running.set()
        while self._running.is_set():
            self.send(body_item.format(json.dumps(self.updater.update())))
            self._tick.clear()
            self._tick.wait(self.interval)


class InputReader(Thread):
    daemon = True
    file = sys.stdin

    def __init__(self, elements: Iterable[BaseElement], output_writer: OutputWriter) -> None:
        super().__init__(name="input")
        self.elements = elements
        self.output_writer = output_writer

    @cached_property
    def elements_by_key(self) -> dict[str, BaseElement]:
        return {key: elem for elem in self.elements if (key := elem.key())}

    @property
    def click_events(self) -> Iterator[dict]:
        assert self.file.readline().strip() == "["
        for line in self.file:
            yield json.loads(line.strip().lstrip(","))

    def run(self) -> None:
        logger.info("Listening for click events from stdin...")

        for click_event in self.click_events:
            logger.debug(f"Received click event: {click_event!r}")

            name = click_event["name"]
            instance = click_event.get("instance")
            key = f"{name}:{instance}" if instance else name

            try:
                element = self.elements_by_key[key]
            except KeyError:
                element = self.elements_by_key[name]

            element.on_click(click_event)
            self.output_writer.update()


def start(elements: Iterable[BaseElement], interval: Seconds, click_events: bool) -> None:
    locale.setlocale(locale.LC_ALL, "")

    updater = Updater(*elements)

    output_writer = OutputWriter(updater, interval, click_events)

    if click_events:
        input_thread = InputReader(elements, output_writer)

    def update(sig, frame):
        logger.info(f"Signal was sent to update: {Signals(sig).name} ({sig})")
        logger.debug(f"Current stack frame: {frame}")
        output_writer.update()

    signal(SIGUSR1, update)

    def shutdown(sig, frame):
        logger.info(f"Signal was sent to shutdown: {Signals(sig).name} ({sig})")
        logger.debug(f"Current stack frame: {frame}")
        output_writer.stop()

    signal(SIGINT, shutdown)
    signal(SIGTERM, shutdown)

    if click_events:
        input_thread.start()

    output_writer.start()
