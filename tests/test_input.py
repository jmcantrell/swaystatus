import dataclasses
import json
from io import StringIO
from operator import itemgetter
from random import shuffle
from subprocess import Popen
from typing import IO, Callable, Iterable

from swaystatus.click_event import ClickEvent
from swaystatus.element import BaseElement
from swaystatus.input import InputProcessor

from .fake import fake_click_event


def create_input_file(click_events: Iterable[ClickEvent]) -> IO[str]:
    input_file = StringIO()
    input_file.write("[\n")
    for click_event in click_events:
        input_file.write(f",{json.dumps(click_event.as_dict())}\n")
    input_file.seek(0)
    return input_file


def test_input_process_click_handler_delegation() -> None:
    """Ensure that clicks are sent to the correct handler."""
    actual_clicks = []

    def handler_func() -> bool:
        return True

    handler_process = Popen("true")

    class Element(BaseElement):
        name = "test"

        def register_click(self, click_event: ClickEvent) -> None:
            nonlocal actual_clicks
            actual_clicks.append(click_event)

        def on_click_1(self, click_event: ClickEvent) -> None:
            self.register_click(click_event)

        def on_click_2(self, click_event: ClickEvent) -> bool:
            self.register_click(click_event)
            return True

        def on_click_3(self, click_event: ClickEvent) -> Callable[[], bool]:
            self.register_click(click_event)
            return handler_func

        def on_click_4(self, click_event: ClickEvent) -> Popen:
            self.register_click(click_event)
            return handler_process

    element = Element()
    expected_processed = [
        (
            dataclasses.replace(
                fake_click_event,
                name="test",
                button=button,
            ),
            element,
            handler_result,
        )
        for button, handler_result in enumerate(
            [
                None,
                True,
                handler_func,
                handler_process,
            ],
            start=1,
        )
    ]
    shuffle(expected_processed)
    expected_clicks = list(map(itemgetter(0), expected_processed))
    input_file = create_input_file(expected_clicks)
    input_processor = InputProcessor([element])
    actual_processed = list(input_processor.process(input_file))
    assert actual_clicks == expected_clicks
    assert actual_processed == expected_processed


def test_input_process_element_delegation() -> None:
    """Ensure that clicks are sent to the correct element."""
    actual_clicks = []

    class Element(BaseElement):
        def on_click_1(self, click_event: ClickEvent) -> None:
            nonlocal actual_clicks
            actual_clicks.append(click_event)

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
    expected_processed = [
        (
            dataclasses.replace(
                fake_click_event,
                name=element.name,
                instance=element.instance,
                button=1,
            ),
            element,
            None,
        )
        for element in elements
    ]
    shuffle(expected_processed)
    expected_clicks = list(map(itemgetter(0), expected_processed))
    input_file = create_input_file(expected_clicks)
    input_processor = InputProcessor(elements)
    actual_processed = list(input_processor.process(input_file))
    assert actual_clicks == expected_clicks
    assert actual_processed == expected_processed
