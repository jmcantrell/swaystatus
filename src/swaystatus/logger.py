import threading
from logging import WARNING, Filter, Formatter, LogRecord, StreamHandler, basicConfig, getLogger

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
