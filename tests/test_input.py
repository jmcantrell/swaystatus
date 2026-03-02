import json
from io import StringIO
from itertools import repeat
from random import shuffle
from types import MethodType
from typing import IO, Iterable, Self
from unittest import TestCase, main

from swaystatus.click_event import ClickEvent
from swaystatus.element import BaseElement
from swaystatus.input import InputProcessor, click_events
from tests.fake import fake_click_event


def create_input_file(click_events: Iterable[ClickEvent]) -> IO[str]:
    input_file = StringIO()
    input_file.write("[\n")
    for click_event in click_events:
        input_file.write(f",{json.dumps(click_event.as_dict())}\n")
    input_file.seek(0)
    return input_file


class TestClickEvents(TestCase):
    def test_parse(self) -> None:
        """Test that click events can be parsed from an IO stream."""
        expected = [fake_click_event(name=name) for name in "abc"]
        self.assertListEqual(list(click_events(create_input_file(expected))), expected)


class TestInputProcessor(TestCase):
    def test_process_element_delegation(self) -> None:
        """Test that click events are sent to the correct element."""

        actual_click_events = []

        class Element(BaseElement):
            def on_click_1(element: Self, click_event: ClickEvent) -> None:
                nonlocal actual_click_events
                actual_click_events.append(click_event)
                self.assertEqual(click_event.button, 1)
                self.assertEqual(click_event.name, element.name)
                self.assertEqual(click_event.instance, element.instance)

        class Element1(Element):
            name = "test1"

        class Element2(Element):
            name = "test2"

        elements = [
            Element1(),
            Element1(instance="a"),
            Element1(instance="b"),
            Element2(),
            Element2(instance="a"),
            Element2(instance="b"),
        ]
        expected_click_events = [
            fake_click_event(
                name=element.name,
                instance=element.instance,
                button=1,
            )
            for element in elements
        ]
        shuffle(expected_click_events)
        input_file = create_input_file(expected_click_events)
        self.assertListEqual(
            list(InputProcessor(elements).process(input_file)),
            list(repeat(False, len(expected_click_events))),
        )
        self.assertListEqual(actual_click_events, expected_click_events)

    def test_process_handler_delegation(self) -> None:
        """Test that click events are sent to the correct element handler."""

        class Element(BaseElement):
            name = "test"

        element = Element()
        buttons = list(range(1, 4))
        actual_click_events = []

        def set_click_handler(button: int) -> None:

            def click_handler(element: Element, click_event: ClickEvent) -> None:
                nonlocal actual_click_events
                actual_click_events.append(click_event)
                self.assertEqual(click_event.button, button)
                self.assertEqual(click_event.name, element.name)
                self.assertEqual(click_event.instance, element.instance)

            setattr(element, f"on_click_{button}", MethodType(click_handler, element))

        for button in buttons:
            set_click_handler(button)

        expected_click_events = [
            fake_click_event(
                name="test",
                button=button,
            )
            for button in buttons
        ]
        shuffle(expected_click_events)
        input_file = create_input_file(expected_click_events)
        self.assertListEqual(
            list(InputProcessor([element]).process(input_file)),
            list(repeat(False, len(expected_click_events))),
        )
        self.assertListEqual(actual_click_events, expected_click_events)


if __name__ == "__main__":
    main()
