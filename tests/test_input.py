import itertools
import json
import logging
import random
from io import StringIO
from typing import IO, Iterable
from unittest import TestCase, main
from unittest.mock import MagicMock, Mock

from swaystatus.click_event import ClickEvent
from swaystatus.element import BaseElement
from swaystatus.input import InputDriver, InputProcessor
from swaystatus.logging import logger
from swaystatus.status_line import StatusLine


def dummy_click_event(name: str | None, instance: str | None) -> ClickEvent:
    return ClickEvent(
        name=name,
        instance=instance,
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
        on_click_mock = Mock()

        class Element(BaseElement):
            def on_click_1(self, click_event: ClickEvent) -> bool:
                return on_click_mock(self, click_event)

        elements = [
            Element("test1"),
            Element("test1", "a"),
            Element("test1", "b"),
            Element("test2"),
            Element("test2", "a"),
            Element("test2", "b"),
        ]
        expected_click_events = [dummy_click_event(element.name, element.instance) for element in elements]
        random.shuffle(expected_click_events)
        expected_updates = [random.choice([True, False]) for _ in range(len(elements))]
        on_click_mock.side_effect = expected_updates

        update_mock = Mock()
        expected_update_calls = sum(1 for u in expected_updates if u)

        status_line = StatusLine(elements)
        input_file = fake_input_file(expected_click_events)
        input_processor = InputProcessor(input_file, status_line, update_mock)

        with self.assertLogs(logger, logging.INFO) as logged:
            actual_processed = list(input_processor)

        actual_clicked_elements = [c.args[0] for c in on_click_mock.call_args_list]

        self.assertEqual(len(expected_click_events), len(logged.records))
        for click_event, element, log_record in zip(expected_click_events, actual_clicked_elements, logged.records):
            self.assertEqual(log_record.levelno, logging.INFO)
            self.assertEqual(log_record.message, f"sending {click_event} to {element}")

        actual_click_events = [c.args[1] for c in on_click_mock.call_args_list]

        self.assertEqual(actual_processed, expected_click_events)
        self.assertEqual(actual_click_events, expected_click_events)
        self.assertEqual(update_mock.call_count, expected_update_calls)

    def test_click_event_no_name(self) -> None:
        status_line = StatusLine([])
        click_event = dummy_click_event(None, None)
        input_file = fake_input_file([click_event])
        input_processor = InputProcessor(input_file, status_line, lambda: None)

        with self.assertLogs(logger, logging.WARNING) as logged:
            self.assertEqual(list(input_processor), [])

        self.assertEqual(len(logged.records), 1)
        self.assertEqual(logged.records[0].levelno, logging.WARNING)
        self.assertEqual(logged.records[0].message, f"unidentified {click_event}")

    def test_click_event_no_target(self) -> None:
        status_line = StatusLine([])
        click_event = dummy_click_event("clock", None)
        input_file = fake_input_file([click_event])
        input_processor = InputProcessor(input_file, status_line, lambda: None)

        with self.assertLogs(logger, logging.WARNING) as logged:
            self.assertEqual(list(input_processor), [])

        self.assertEqual(len(logged.records), 1)
        self.assertEqual(logged.records[0].levelno, logging.WARNING)
        self.assertEqual(logged.records[0].message, f"no element to handle {click_event}")


class TestInputDriver(TestCase):
    def test_iterates_eagerly(self) -> None:
        click_event = dummy_click_event("test", None)
        expected_calls = random.randint(2, 10)
        expected_messages = [f"processed input: {click_event!r}"] * expected_calls
        iter_mock = MagicMock()
        iter_mock.__iter__.return_value = itertools.repeat(click_event, expected_calls)

        with self.assertLogs(logger, logging.DEBUG) as logged:
            input_driver = InputDriver(iter_mock)
            input_driver.start()
            input_driver.join(timeout=1.0)

        self.assertEqual(list(iter_mock), [], "expected iterator to be exhausted")
        actual_messages = [r.message for r in logged.records]
        self.assertEqual(actual_messages, expected_messages)


if __name__ == "__main__":
    main()
