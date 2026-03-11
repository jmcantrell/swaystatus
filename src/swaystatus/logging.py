import threading
from logging import WARNING, Formatter, StreamHandler, basicConfig, getLogger

handler = StreamHandler()
handler.setFormatter(Formatter("%(name)s: %(threadName)s: %(levelname)s: %(message)s"))
basicConfig(level=WARNING, handlers=[handler])

logger = getLogger(__package__)


def excepthook(args):
    logger.exception(
        "unhandled exception in thread: %s",
        args.thread.name,
        exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
    )


threading.excepthook = excepthook
