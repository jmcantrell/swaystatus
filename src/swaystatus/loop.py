import sys
import locale
import json
import shlex
import subprocess
from signal import signal, SIGUSR1
from threading import Thread
from types import MethodType
from .updater import Updater
from .modules import Modules


def set_click_event_handler(element, button, command):
    if not isinstance(command, list):
        command = shlex.split(command)

    def handler(self, event):
        subprocess.run(command)

    setattr(element, f"on_click_{button}", MethodType(handler, element))


def generate_elements(config):
    modules = Modules(config["include"])
    module_settings = config.get("settings", {})
    on_click_handlers = config.get("on_click", {})

    for module_name in config.get("order", []):
        element = modules.find(module_name).Element(
            **module_settings.get(module_name, {})
        )

        for button, command in on_click_handlers.get(module_name, {}).items():
            set_click_event_handler(element, button, command)

        element.name = module_name

        yield element


def run(config):
    locale.setlocale(locale.LC_ALL, "")

    elements = list(generate_elements(config))

    elements_by_name = {
        element.name: element
        for element in elements
        if hasattr(element, "name")
    }

    updater = Updater(elements, **config)

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
