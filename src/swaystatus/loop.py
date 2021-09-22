import sys
import locale
import json
from threading import Thread
from .updater import Updater


def run(config):
    locale.setlocale(locale.LC_ALL, "")

    elements_by_name = {
        element.name: element
        for element in config.elements
        if hasattr(element, "name")
    }

    def stdout():
        Updater(config.elements, interval=config.interval).run()

    stdout_thread = Thread(target=stdout)
    stdout_thread.daemon = True
    stdout_thread.start()

    # Discard the opening '['.
    sys.stdin.readline()

    for line in sys.stdin:
        click_event = json.loads(line.lstrip(","))
        elements_by_name[click_event["name"]].on_click(click_event)
