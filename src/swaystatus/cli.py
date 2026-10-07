"""The primary application interface is at the command line."""

from .app import App
from .logger import logger


def main() -> int:
    """
    Start continuous status line generation.

    Return an integer to dictate the process exit status. On clean shutdown,
    return zero (success). Errors will be logged before returning non-zero
    (failure).
    """
    try:
        App().run()
    except Exception:
        logger.exception("unhandled exception in app")
        return 1
    return 0
