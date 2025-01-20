import json
import locale
import sys

from signal import signal, Signals, SIGINT, SIGTERM, SIGUSR1
from threading import Thread

from .logging import logger
from .updater import Updater


def configure_signal_handlers(updater):
    def update(sig, frame):
        logger.info(f"Signal was sent to update: {Signals(sig).name} ({sig})")
        logger.debug(f"Current stack frame: {frame}")
        try:
            updater.update()
        except Exception:
            logger.exception("Unhandled exception while updating status bar")
            sys.exit(1)

    def shutdown(sig, frame):
        logger.info(f"Signal was sent to shutdown: {Signals(sig).name} ({sig})")
        logger.debug(f"Current stack frame: {frame}")
        try:
            updater.stop()
        except Exception:
            logger.exception("Unhandled exception while shutting down")
            sys.exit(1)

    signal(SIGUSR1, update)
    signal(SIGINT, shutdown)
    signal(SIGTERM, shutdown)


def start_stdout_thread(updater):
    def write_to_stdout():
        try:
            updater.start()
        except Exception:
            logger.exception("Unhandled exception in stdout writer thread")
            sys.exit(1)

    stdout_thread = Thread(target=write_to_stdout)
    stdout_thread.start()
    stdout_thread.join()


def start_stdin_thread(updater, elements):
    elements_by_key = {key: elem for elem in elements if (key := elem.key())}

    def read_from_stdin():
        logger.info("Listening for click events from stdin...")
        try:
            assert sys.stdin.readline().strip() == "["

            for line in sys.stdin:
                click_event = json.loads(line.strip().lstrip(","))
                logger.debug(f"Received click event: {click_event!r}")

                name = click_event["name"]
                instance = click_event.get("instance")
                key = f"{name}:{instance}" if instance else name

                try:
                    element = elements_by_key[key]
                except KeyError:
                    element = elements_by_key[name]

                element.on_click(click_event)
                updater.update()

        except Exception:
            logger.exception("Unhandled exception in stdin reader thread")
            sys.exit(1)

    stdin_thread = Thread(target=read_from_stdin)
    stdin_thread.daemon = True
    stdin_thread.start()


def start(elements, interval, click_events):
    locale.setlocale(locale.LC_ALL, "")

    updater = Updater(elements, interval, click_events)

    configure_signal_handlers(updater)

    if click_events:
        start_stdin_thread(updater, elements)

    start_stdout_thread(updater)
