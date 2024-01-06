from logging import getLogger, basicConfig, Formatter, StreamHandler, FileHandler

from .env import bin_name

logger = getLogger(bin_name)


def create_formatter(named=True, timestamped=True):
    fmt = ""

    if timestamped:
        fmt += "%(asctime)s: "

    fmt += "%(levelname)s: "

    if named:
        fmt += "%(name)s: "

    fmt += "%(message)s"

    return Formatter(fmt)


def configure(level=None, file=None, syslog=False):
    handlers = []

    stream_handler = StreamHandler()
    stream_handler.setFormatter(create_formatter())
    handlers.append(stream_handler)

    if file:
        file_handler = FileHandler(file)
        file_handler.setFormatter(create_formatter())
        handlers.append(file_handler)

    if syslog:
        from logging.handlers import SysLogHandler

        syslog_handler = SysLogHandler(address="/dev/log")
        syslog_handler.setFormatter(create_formatter(named=False, timestamped=False))
        syslog_handler.ident = f"{bin_name}: "

        handlers.append(syslog_handler)

    if level and isinstance(level, str):
        level = level.upper()

    basicConfig(level=level, handlers=handlers)
