from signal import SIGCONT, SIGINT, SIGTERM, SIGUSR1, Signals, signal
from types import FrameType

from .config import Config
from .input import InputDelegator
from .logging import logger
from .output import OutputGenerator
from .threading import InputReader, OutputWriter


class App:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.output_writer = OutputWriter(
            OutputGenerator(config.elements, config.click_events),
            config.interval,
        )
        if self.config.click_events:
            self.input_reader = InputReader(
                InputDelegator(config.elements),
                self.output_writer,
            )

    def update(self, sig: int, frame: FrameType | None) -> None:
        logger.info(f"Signal was sent to update: {Signals(sig).name} ({sig})")
        logger.debug(f"Current stack frame: {frame!r}")
        self.output_writer.update()

    def shutdown(self, sig: int, frame: FrameType | None) -> None:
        logger.info(f"Signal was sent to shutdown: {Signals(sig).name} ({sig})")
        logger.debug(f"Current stack frame: {frame!r}")
        self.output_writer.stop()

    def run(self) -> None:
        signal(SIGUSR1, self.update)
        signal(SIGCONT, self.update)
        signal(SIGINT, self.shutdown)
        signal(SIGTERM, self.shutdown)
        if self.input_reader:
            self.input_reader.start()
        self.output_writer.start()


__all__ = [App.__name__]
