from dataclasses import replace
from unittest import TestCase, main

from swaystatus.click_event import ClickEvent

dummy_click_event = ClickEvent(
    name="clock",
    instance="home",
    x=1900,
    y=10,
    button=1,
    event=274,
    relative_x=100,
    relative_y=8,
    width=120,
    height=18,
    scale=0.0,
)


class TestClickEvent(TestCase):
    def test_as_dict(self) -> None:
        exported = replace(dummy_click_event, name=None, instance=None).as_dict()
        self.assertNotIn("name", exported)
        self.assertNotIn("instance", exported)


if __name__ == "__main__":
    main()
