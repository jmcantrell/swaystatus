import dataclasses
import itertools
import json
import random
from io import StringIO
from typing import IO, Iterable
from unittest import TestCase, main
from unittest.mock import MagicMock

from swaystatus.click_event import ClickEvent
from swaystatus.element import BaseElement
from swaystatus.input import InputDriver, InputProcessor, parse_click_events
from swaystatus.status_line import StatusLine

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


def fake_input_file(click_events: Iterable[ClickEvent]) -> IO[str]:
    input_file = StringIO()
    input_file.write("[\n")
    for click_event in click_events:
        input_file.write(f",{json.dumps(click_event.as_dict())}\n")
    input_file.seek(0)
    return input_file


class TestInputProcessor(TestCase):
    def test_element_delegation(self) -> None:
        actual_click_events = []

        class Element(BaseElement):
            def on_click_1(self, click_event: ClickEvent) -> None:
                actual_click_events.append(click_event)

        elements = [
            Element("test"),
            Element("test", "a"),
            Element("test", "b"),
            Element("test"),
            Element("test", "a"),
            Element("test", "b"),
        ]
        expected_click_events = [
            dataclasses.replace(
                dummy_click_event,
                name=element.name,
                instance=element.instance,
            )
            for element in elements
        ]
        random.shuffle(expected_click_events)
        input_file = fake_input_file(expected_click_events)
        status_line = StatusLine(elements)
        input_processor = InputProcessor(input_file, status_line)
        actual_processed = list(input_processor)
        self.assertEqual(actual_processed, expected_click_events)
        self.assertEqual(actual_click_events, expected_click_events)

    def test_parse_click_events(self) -> None:
        click_events = [
            dataclasses.replace(dummy_click_event, name=name, instance=instance)
            for name, instance in itertools.product(["foo", "bar", "baz"], [None, "a", "b"])
        ] * random.randint(1, 5)
        random.shuffle(click_events)
        self.assertEqual(list(parse_click_events(fake_input_file(click_events))), click_events)


class TestInputDriver(TestCase):
    def test_iterates_eagerly(self) -> None:
        expected_calls = random.randint(2, 10)
        iter_mock = MagicMock()
        iter_mock.__iter__.return_value = iter([[]] * expected_calls)
        input_driver = InputDriver(iter_mock)
        input_driver.start()
        input_driver.join(timeout=1.0)
        self.assertEqual(list(iter_mock), [], "expected iterator to be exhausted")


if __name__ == "__main__":
    main()
