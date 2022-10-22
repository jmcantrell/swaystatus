import sys, locale, json
from signal import signal, SIGINT, SIGUSR1
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
            logger.exception("Unhandled exception in stdout writer thread")
            sys.exit(1)

    stdout_thread = Thread(target=write_to_stdout)

    def read_from_stdin():
        logger.info("Listening for click events from stdin...")
        try:
            assert sys.stdin.readline().strip() == "["
            for line in sys.stdin:
                click_event = json.loads(line.strip().lstrip(","))
                logger.debug(f"Received click event: {click_event!r}")
                elements_by_name[click_event["name"]].on_click(click_event)
        except Exception:
            logger.exception("Unhandled exception in stdin reader thread")
            sys.exit(1)

    stdin_thread = Thread(target=read_from_stdin)
    stdin_thread.daemon = True  # so it will terminate when the main thread does

    def update(sig, frame):
        logger.info(f"Signal was sent to update status bar: {sig}")
        logger.debug(f"Current stack frame: {frame}")
        try:
            updater.update()
        except Exception:
            logger.exception("Unhandled exception while updating status bar")
            sys.exit(1)

    def shutdown(sig, frame):
        logger.info(f"Signal was sent to shutdown: {sig}")
        logger.debug(f"Current stack frame: {frame}")
        try:
            updater.stop()
        except Exception:
            logger.exception("Unhandled exception while shutting down")
            sys.exit(1)

    signal(SIGUSR1, update)
    signal(SIGINT, shutdown)

    stdout_thread.start()
    if config["click_events"]:
        stdin_thread.start()

    stdout_thread.join()
