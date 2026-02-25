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
    def test_str(self) -> None:
        self.assertEqual(str(dummy_click_event), "click event button=1 name='clock' instance='home'")


if __name__ == "__main__":
    main()
