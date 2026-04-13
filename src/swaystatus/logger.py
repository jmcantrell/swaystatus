import threading
from collections.abc import Iterator
from contextlib import contextmanager
from logging import WARNING, Filter, Formatter, Logger, LogRecord, StreamHandler, basicConfig, getLogger

from .context import context_var


class LogContextFilter(Filter):
    def filter(self, record: LogRecord):
        record.context = context_var.get() or "default"
        return True


handler = StreamHandler()
handler.setFormatter(Formatter("%(name)s %(process)s %(threadName)s %(context)s %(levelname)s %(message)s"))
basicConfig(level=WARNING, handlers=[handler])

logger = getLogger(__package__)
logger.addFilter(LogContextFilter())


def excepthook(args):
    logger.error(
        "unhandled exception in thread: %s",
        args.thread.name,
        exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
    )


threading.excepthook = excepthook


@contextmanager
def logger_level_at(logger: Logger, level: int | str | None) -> Iterator:
    if level is None:
        yield
        return
    level_save = logger.level
    logger.setLevel(level)
    try:
        yield
    finally:
        logger.setLevel(level_save)
