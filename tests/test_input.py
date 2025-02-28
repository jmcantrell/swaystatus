from dataclasses import replace
from itertools import product
from random import shuffle

from swaystatus import BaseElement, ClickEvent
from swaystatus.input import InputDelegator

from .fake import click_event


def test_input_delegation(click_events_file) -> None:
    """Ensure that clicks are sent to the correct element in the same order."""
    actual_clicks: list[tuple[str, str | None, int]] = []

    class Element(BaseElement):
        def on_click_1(self, event: ClickEvent):
            actual_clicks.append((self.name, self.instance, 1))

        def on_click_2(self, event: ClickEvent):
            actual_clicks.append((self.name, self.instance, 2))

    elements: list[BaseElement] = []
    expected_events: list[ClickEvent] = []
    for name, instance, button in product(["test1", "test2"], [None, "variant"], [1, 2]):
        element = Element()
        element.name = name
        element.instance = instance
        elements.append(element)
        expected_events.append(
            replace(
                click_event,
                name=name,
                instance=instance,
                button=button,
            )
        )
    shuffle(expected_events)
    input_file = click_events_file(expected_events)
    input_delegator = InputDelegator(elements)
    actual_events = [e for e, r in input_delegator.process(input_file)]
    assert actual_events == expected_events
    expected_clicks = [(e.name, e.instance, e.button) for e in expected_events]
    assert actual_clicks == expected_clicks
