"""The logger is used to report activity during runtime."""

import logging
import threading
from collections.abc import Generator
from contextlib import contextmanager

from .context import context_var

logger = logging.getLogger(__package__)

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(name)s %(process)s %(threadName)s %(context)s %(levelname)s %(message)s"))

logging.basicConfig(level=logging.WARNING, handlers=[handler])


class LogContextFilter(logging.Filter):
    """Attach the runtime context to log records."""

    def filter(self, record: logging.LogRecord):
        record.context = context_var.get() or "default"
        return True


logger.addFilter(LogContextFilter())


def excepthook(args):
    """Log any unhandled exceptions that occur during thread execution."""
    logger.error(
        "unhandled exception in thread: %s",
        args.thread.name,
        exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
    )


threading.excepthook = excepthook


@contextmanager
def logger_level_at(level: int | str | None) -> Generator:
    """Change a logger's threshold during execution of a block."""

    if level is None:
        yield
        return

    level_save = logger.level
    logger.setLevel(level)
    try:
        yield
    finally:
        logger.setLevel(level_save)
