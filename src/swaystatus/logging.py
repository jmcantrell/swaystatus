from logging import Formatter, StreamHandler, basicConfig, getLogger

from .env import self_name

logger = getLogger(self_name)
log_format = "%(name)s: %(levelname)s: %(message)s"


def configure_logging(level_name: str) -> None:
    handler = StreamHandler()
    handler.setFormatter(Formatter(log_format))
    basicConfig(level=level_name.upper(), handlers=[handler])
