from .config import Config
from .input import InputDelegator
from .logging import logger
from .output import OutputGenerator
from .threading import InputReader, OutputWriter


class Daemon:
    def __init__(self, config: Config) -> None:
        self.output_writer = OutputWriter(OutputGenerator(config.elements, config.click_events), config.interval)
        if config.click_events:
            self.input_reader = InputReader(InputDelegator(config.elements), self.output_writer)

    def update(self) -> None:
        logger.info("Updating status line")
        self.output_writer.update()

    def stop(self) -> None:
        logger.info("Stopping daemon")
        self.output_writer.stop()

    def start(self) -> None:
        logger.info("Starting daemon")
        if self.input_reader:
            self.input_reader.start()
        self.output_writer.start()


__all__ = [Daemon.__name__]
