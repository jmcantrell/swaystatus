import os
import toml


class Config:
    def __init__(self, file):
        data = toml.loads(open(file).read()) if os.path.isfile(file) else {}
        self.order = data.get("order", [])
        self.interval = data.get("interval", 1)
        self.include = data.get("include", [])
        self.settings = data.get("settings", {})
        self.click_events = data.get("click_events", True)
