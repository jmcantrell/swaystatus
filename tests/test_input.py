import dataclasses
import itertools
import json
import random
from io import StringIO
from typing import IO, Iterable

from pytest_mock import MockerFixture

from swaystatus.click_event import ClickEvent
from swaystatus.element import BaseElement
from swaystatus.input import InputProcessor, parse_click_events
from swaystatus.status_line import StatusLine


def fake_input_file(click_events: Iterable[ClickEvent]) -> IO[str]:
    input_file = StringIO()
    input_file.write("[\n")
    for click_event in click_events:
        input_file.write(f",{json.dumps(click_event.as_dict())}\n")
    input_file.seek(0)
    return input_file


def test_input_process_element_delegation(mocker: MockerFixture, dummy_click_event: ClickEvent) -> None:
    """Click events are sent to the correct element."""
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
    assert actual_processed == expected_click_events
    assert actual_click_events == expected_click_events


def test_parse_click_events(dummy_click_event: ClickEvent) -> None:
    """Click events can be parsed from an IO stream."""
    click_events = [
        dataclasses.replace(dummy_click_event, name=name, instance=instance)
        for name, instance in itertools.product(["foo", "bar", "baz"], [None, "a", "b"])
    ] * random.randint(1, 5)
    random.shuffle(click_events)
    assert list(parse_click_events(fake_input_file(click_events))) == click_events
