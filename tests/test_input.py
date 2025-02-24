from dataclasses import replace
from itertools import product
from random import shuffle

from swaystatus import BaseElement, ClickEvent
from swaystatus.input import InputDelegator

from .fake import click_event


def test_input_delegation(click_events_file) -> None:
    """Ensure that clicks are sent to the correct element in the same order."""
    clicks: list[tuple[str, str | None, int]] = []

    class Element(BaseElement):
        def on_click_1(self, event: ClickEvent):
            clicks.append((self.name, self.instance, 1))

        def on_click_2(self, event: ClickEvent):
            clicks.append((self.name, self.instance, 2))

    events: list[ClickEvent] = []
    elements: list[BaseElement] = []

    for name, instance, button in product(["test1", "test2"], [None, "variant"], [1, 2]):
        element = Element()
        element.name = name
        element.instance = instance
        elements.append(element)

        events.append(
            replace(
                click_event,
                name=name,
                instance=instance,
                button=button,
            )
        )

    shuffle(events)

    input_file = click_events_file(events)
    input_delegator = InputDelegator(elements)
    assert list(input_delegator.process(input_file)) == events
    assert clicks == [(e.name, e.instance, e.button) for e in events]
