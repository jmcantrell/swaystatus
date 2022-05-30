import os
import subprocess
from types import MethodType


class Element:
    name = None

    def __init__(self, *args, **kwargs):
        super().__init__()

        self.intervals = []

        self.env = kwargs.get("env", {})

        for button, handler in kwargs.get("on_click", {}).items():
            self._set_on_click_handler(button, handler)

    def _set_on_click_handler(self, button, handler):
        if not callable(handler):

            def method(self, event):
                env = os.environ.copy()
                env.update(self.env)
                env.update(
                    {
                        key: str(value if value is not None else "")
                        for key, value in event.items()
                    }
                )
                subprocess.run(handler, shell=True, env=env)

        else:

            def method(self, event):
                handler(event)

        setattr(self, f"on_click_{button}", MethodType(method, self))

    def create_block(self, full_text, **params):
        block = {"full_text": full_text}
        block.update(params)

        if self.name:
            block["name"] = self.name

        return block

    def set_interval(self, seconds, options=None):
        self.intervals.append((seconds, options))

    def on_interval(self, options=None):
        pass

    def on_update(self, output):
        pass

    def on_click(self, event):
        try:
            getattr(self, f"on_click_{event['button']}")(event)
            self.updater.update()
        except AttributeError:
            pass
