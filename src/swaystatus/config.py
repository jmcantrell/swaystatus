import toml
from schema import Schema, Optional, And, Or, Use


def positive(number):
    assert number > 0
    return number


schema = Schema(
    {
        "order": [str],
        Optional("click_events"): bool,
        Optional("include"): [str],
        Optional("interval"): Use(float),
        Optional("settings"): Or(
            {
                str: Or(
                    {
                        Optional(str): object,
                    },
                    {},
                ),
            },
            {},
        ),
        Optional("on_click"): Or(
            {
                str: Or(
                    {
                        And(Use(int), Use(positive)): Or([Use(str)], Use(str)),
                    },
                    {},
                )
            },
            {},
        ),
    },
    ignore_extra_keys=True,
)


class Config(dict):
    def read_file(self, file):
        self.update(schema.validate(toml.loads(open(file).read())))
