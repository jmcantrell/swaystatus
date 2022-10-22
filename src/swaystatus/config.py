import toml


default_config = {
    "env": {},
    "order": [],
    "interval": 1.0,
    "include": [],
    "click_events": True,
    "on_click": {},
    "settings": {},
}


class Config(dict):
    def __init__(self, **kwargs):
        super().__init__()
        self.update(default_config)
        self.update(kwargs)

    def read_file(self, file):
        self.update(toml.loads(open(file).read()))
