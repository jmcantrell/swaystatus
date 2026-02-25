from .app import App
from .logger import logger


def main() -> int:
    try:
        App().run()
    except Exception:
        logger.exception("unhandled exception in app")
        return 1
    return 0
