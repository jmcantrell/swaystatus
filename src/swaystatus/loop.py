import sys, locale, json
from signal import signal, SIGUSR1
from threading import Thread
from _thread import interrupt_main
from .updater import Updater
from .logging import logger


def run(elements, **config):
    locale.setlocale(locale.LC_ALL, "")

    elements_by_name = {
        element.name: element
        for element in elements
        if hasattr(element, "name")
    }

    updater = Updater(elements, **config)

    def stdout():
        try:
            updater.run()
        except Exception as e:
            logger.exception("unhandled exception in output thread")
            interrupt_main()

    def update(*args, **kwargs):
        try:
            updater.update()
        except Exception as e:
            logger.exception("unhandled exception when updating")
            sys.exit(1)

    signal(SIGUSR1, update)

    stdout_thread = Thread(target=stdout)
    stdout_thread.daemon = True
    stdout_thread.start()

    # Discard the opening '['.
    sys.stdin.readline()

    for line in sys.stdin:
        click_event = json.loads(line.lstrip(","))
        try:
            elements_by_name[click_event["name"]].on_click(click_event)
        except Exception as e:
            logger.exception("unhandled exception during click event")
            sys.exit(1)
