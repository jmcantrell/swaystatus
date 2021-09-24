class BaseElement:
    def __init__(self):
        super().__init__()
        self.intervals = []

    def create_block(self, full_text, **kwargs):
        kwargs["full_text"] = full_text

        if hasattr(self, "name"):
            kwargs["name"] = self.name

        return kwargs

    def set_interval(self, seconds, options=None):
        self.intervals.append((seconds, options))

    def on_interval(self, options=None):
        pass

    def on_update(self, output):
        raise NotImplementedError

    def on_click(self, event):
        try:
            getattr(self, f"on_click_{event['button']}")(event)
            self.updater.update()
        except AttributeError:
            pass
