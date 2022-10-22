import sys, locale, json
from signal import signal, SIGINT, SIGTSTP, SIGUSR1
from threading import Thread
from .updater import Updater
from .logging import logger


def start(elements, **config):
    locale.setlocale(locale.LC_ALL, "")

    elements_by_name = {element.name: element for element in elements if hasattr(element, "name")}

    updater = Updater(elements, **config)

    def write_to_stdout():
        try:
            updater.start()
        except Exception:
            logger.exception("Unhandled exception in output thread")

    stdout_thread = Thread(target=write_to_stdout)

    def update(sig, frame):
        logger.info(f"Signal was sent to refresh: {sig}")
        logger.debug(f"Current stack frame: {frame}")
        try:
            updater.update()
        except Exception:
            logger.exception("Unhandled exception when updating")
            sys.exit(1)

    def stop(sig, frame):
        logger.info(f"Signal was sent to shutdown: {sig}")
        logger.debug(f"Current stack frame: {frame}")
        try:
            updater.stop()
        except Exception:
            logger.exception("Unhandled exception when stopping")
            sys.exit(1)
        sys.exit(0)

    signal(SIGUSR1, update)
    signal(SIGTSTP, stop)
    signal(SIGINT, stop)

    stdout_thread.start()

    if config["click_events"]:
        # Discard the opening '['.
        sys.stdin.readline()

        for line in sys.stdin:
            click_event = json.loads(line.lstrip(","))
            logger.debug(f"Received click event: {click_event!r}")
            try:
                elements_by_name[click_event["name"]].on_click(click_event)
            except Exception:
                logger.exception(f"Unhandled exception during click event: {click_event!r}")
                sys.exit(1)

    stdout_thread.join()
