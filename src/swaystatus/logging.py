from logging import getLogger, basicConfig, Formatter, StreamHandler, FileHandler

try:
    from systemd.journal import JournalHandler
except ModuleNotFoundError:
    journal_available = False
else:
    journal_available = True

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


def configure(level=None, file=None, journal=False):
    handlers = []

    stream_handler = StreamHandler()
    stream_handler.setFormatter(create_formatter())
    handlers.append(stream_handler)

    if file:
        file_handler = FileHandler(file)
        file_handler.setFormatter(create_formatter())
        handlers.append(file_handler)

    if journal_available and journal:
        journal_handler = JournalHandler(SYSLOG_IDENTIFIER=logger.name)
        journal_handler.setFormatter(create_formatter(named=False, timestamped=False))
        handlers.append(journal_handler)

    if level and isinstance(level, str):
        level = level.upper()

    basicConfig(level=level, handlers=handlers)
