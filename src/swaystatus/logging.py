from logging import Formatter, StreamHandler, basicConfig, getLogger

from .env import self_name

logger = getLogger(self_name)


def configure(level: str) -> None:
    stream_handler = StreamHandler()
    stream_handler.setFormatter(Formatter("%(name)s: %(levelname)s: %(message)s"))
    basicConfig(level=level.upper(), handlers=[stream_handler])
