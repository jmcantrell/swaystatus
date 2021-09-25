import sys
import locale
import json
from signal import signal, SIGUSR1
from threading import Thread
from .updater import Updater


def run(elements, **options):
    locale.setlocale(locale.LC_ALL, "")

    elements_by_name = {
        element.name: element
        for element in elements
        if hasattr(element, "name")
    }

    updater = Updater(elements, **options)

    def stdout():
        updater.run()

    def update(*args, **kwargs):
        updater.update()

    signal(SIGUSR1, update)

    stdout_thread = Thread(target=stdout)
    stdout_thread.daemon = True
    stdout_thread.start()

    # Discard the opening '['.
    sys.stdin.readline()

    for line in sys.stdin:
        click_event = json.loads(line.lstrip(","))
        elements_by_name[click_event["name"]].on_click(click_event)
