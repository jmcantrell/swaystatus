import dataclasses
import itertools
import json
import random
from io import StringIO
from typing import IO, Callable, Iterable

from pytest import fixture
from pytest_mock import MockerFixture

from swaystatus.click_event import ClickEvent
from swaystatus.element import BaseElement
from swaystatus.input import InputProcessor, parse_click_events

type InputFileFactory = Callable[[Iterable[ClickEvent]], IO[str]]


@fixture
def input_file_factory() -> InputFileFactory:
    def factory(click_events: Iterable[ClickEvent]) -> IO[str]:
        input_file = StringIO()
        input_file.write("[\n")
        for click_event in click_events:
            input_file.write(f",{json.dumps(click_event.as_dict())}\n")
        input_file.seek(0)
        return input_file

    return factory


def test_input_process_element_delegation(
    mocker: MockerFixture,
    dummy_click_event: ClickEvent,
    input_file_factory: InputFileFactory,
) -> None:
    """Test that click events are sent to the correct element."""
    actual_click_events = []

    class Element(BaseElement):
        def on_click_1(self, click_event: ClickEvent) -> None:
            actual_click_events.append(click_event)

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
        dataclasses.replace(
            dummy_click_event,
            name=element.name,
            instance=element.instance,
        )
        for element in elements
    ]
    random.shuffle(expected_click_events)
    input_file = input_file_factory(expected_click_events)
    input_processor = InputProcessor(elements)
    processed_updates = list(input_processor.process(input_file))
    assert actual_click_events == expected_click_events
    assert processed_updates == [False] * len(expected_click_events)


def test_parse_click_events(dummy_click_event: ClickEvent, input_file_factory: InputFileFactory) -> None:
    """Test that click events can be parsed from an IO stream."""
    click_events = [
        dataclasses.replace(dummy_click_event, name=name, instance=instance)
        for name, instance in itertools.product(["foo", "bar", "baz"], [None, "a", "b"])
    ] * random.randint(1, 5)
    random.shuffle(click_events)
    assert list(parse_click_events(input_file_factory(click_events))) == click_events
