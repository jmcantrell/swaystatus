from .element import BaseElement
from .input import InputDelegator
from .output import OutputGenerator
from .threading import InputReader, OutputWriter


class Daemon:
    def __init__(self, elements: list[BaseElement], interval: float, click_events: bool) -> None:
        self.output_writer = OutputWriter(OutputGenerator(elements, click_events), interval)
        if click_events:
            self.input_reader = InputReader(InputDelegator(elements), self.output_writer)

    def update(self) -> None:
        self.output_writer.update()

    def stop(self) -> None:
        self.output_writer.stop()

    def start(self) -> None:
        if self.input_reader:
            self.input_reader.start()
        self.output_writer.start()


__all__ = [Daemon.__name__]
