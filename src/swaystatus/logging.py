import threading
from logging import Formatter, StreamHandler, basicConfig, getLogger

from .env import self_name

logger = getLogger(self_name)
log_format = "%(name)s: %(threadName)s: %(levelname)s: %(message)s"


def excepthook(args):
    logger.exception(
        "unhandled exception in thread: %s",
        args.thread.name,
        exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
    )


threading.excepthook = excepthook


def configure_logging(level_name: str) -> None:
    handler = StreamHandler()
    handler.setFormatter(Formatter(log_format))
    basicConfig(level=level_name.upper(), handlers=[handler])
