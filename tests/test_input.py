import json
import logging
import random
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import asdict
from io import StringIO
from itertools import batched, repeat
from threading import Event
from unittest import TestCase, main
from unittest.mock import MagicMock, Mock, patch

from swaystatus.click_event import ClickEvent
from swaystatus.element import BaseElement, UpdateHandler
from swaystatus.input import InputDriver, InputProcessor
from swaystatus.logger import logger


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


def fake_input_lines(click_events: Iterable[ClickEvent]) -> Iterator[str]:
    yield "[\n"
    for click_event in click_events:
        yield f",{json.dumps(asdict(click_event))}\n"


class TestInputProcessor(TestCase):
    def setUp(self) -> None:
        self.stdin = StringIO()
        stdin_patcher = patch("sys.stdin", self.stdin)
        stdin_patcher.start()
        self.addCleanup(stdin_patcher.stop)

    def set_input(self, click_events: Iterable[ClickEvent]) -> None:
        pos = self.stdin.tell()
        self.stdin.writelines(fake_input_lines(click_events))
        self.stdin.seek(pos)

    def test_click_target(self) -> None:
        element = BaseElement("test")
        element_a = BaseElement("test", "a")
        elements = [element, element_a]
        input_processor = InputProcessor(elements, lambda: None)
        self.assertIs(input_processor.click_target("test"), element)
        self.assertIs(input_processor.click_target("test", "a"), element_a)
        self.assertIs(input_processor.click_target("test", "b"), element)

    def test_element_delegation(self) -> None:
        on_click_mock = Mock(return_value=False)

        class Element(BaseElement):
            def on_click_1(self, click_event: ClickEvent) -> bool:
                return on_click_mock(self)

        elements = [
            Element("test1"),
            Element("test1", "a"),
            Element("test1", "b"),
            Element("test2"),
            Element("test2", "a"),
            Element("test2", "b"),
        ]

        expected_click_events = [dummy_click_event(e.name, e.instance) for e in elements]
        random.shuffle(expected_click_events)
        self.set_input(expected_click_events)

        update_mock = Mock()
        input_processor = InputProcessor(elements, update_mock)

        with self.assertLogs(logger, logging.INFO) as logged:
            actual_click_events = list(input_processor)

        self.assertEqual(actual_click_events, expected_click_events)
        update_mock.assert_not_called()

        for i, (click_event, log_records) in enumerate(
            zip(expected_click_events, batched(logged.records, n=2, strict=True), strict=True)
        ):
            self.assert_click_context(log_records)
            record_recv, record_send = log_records
            self.assertEqual(record_recv.levelno, logging.INFO)
            self.assertEqual(record_recv.message, f"received {click_event}")
            self.assertEqual(record_send.levelno, logging.INFO)
            self.assertEqual(record_send.message, f"sending to {on_click_mock.call_args_list[i].args[0]}")

    def test_click_event_no_name(self) -> None:
        click_event = dummy_click_event(None, None)
        self.set_input([click_event])
        input_processor = InputProcessor([], lambda: None)

        with self.assertLogs(logger, logging.WARNING) as logged:
            self.assertEqual(list(input_processor), [])

        self.assertEqual(len(logged.records), 1)
        self.assertEqual(logged.records[0].levelno, logging.WARNING)
        self.assertEqual(logged.records[0].message, "click event missing element name")

    def test_click_event_no_target(self) -> None:
        click_event = dummy_click_event("clock", None)
        self.set_input([click_event])
        input_processor = InputProcessor([], lambda: None)

        with self.assertLogs(logger, logging.WARNING) as logged:
            self.assertEqual(list(input_processor), [])

        self.assertEqual(len(logged.records), 1)
        self.assertEqual(logged.records[0].levelno, logging.WARNING)
        self.assertEqual(logged.records[0].message, "target element not found")

    def test_update(self) -> None:
        click_event = dummy_click_event("clock", None)

        class Element(BaseElement):
            def on_click_1(self, click_event: ClickEvent) -> bool:
                return update

        for update in [True, False]:
            with self.subTest(update=update):
                self.set_input([click_event])
                updater_mock = Mock()
                input_processor = InputProcessor([Element("clock")], updater_mock)
                with self.assertLogs(logger, level=logging.INFO) as logged:
                    self.assertEqual(list(input_processor), [click_event])
                self.assert_click_context(logged.records)
                if update:
                    self.assertEqual(logged.records[-1].message, "updating")
                    updater_mock.assert_called_once()
                else:
                    updater_mock.assert_not_called()

    def test_update_handler(self) -> None:
        click_event = dummy_click_event("clock", None)
        update_handler_called = Event()

        def update_handler_inner() -> bool:
            update_handler_called.set()
            return update

        class Element(BaseElement):
            def on_click_1(self, click_event: ClickEvent) -> UpdateHandler:
                return update_handler_inner

        for update in [True, False]:
            with self.subTest(update=update):
                self.set_input([click_event])
                updater_mock = Mock()
                update_handler_called.clear()
                input_processor = InputProcessor([Element("clock")], updater_mock)
                with self.assertLogs(logger, level=logging.INFO) as logged:
                    self.assertEqual(list(input_processor), [click_event])
                    update_handler_called.wait(timeout=1.0)
                self.assert_click_context(logged.records)
                if update:
                    self.assertEqual(logged.records[-1].message, "updating")
                    updater_mock.assert_called_once()
                else:
                    updater_mock.assert_not_called()

    def assert_click_context(self, log_records: Sequence[logging.LogRecord]) -> None:
        assert log_records
        first_record = log_records[0]
        assert hasattr(first_record, "context") and isinstance(first_record.context, str)
        self.assertTrue(first_record.context.startswith("click event"))
        for log_record in log_records:
            assert hasattr(log_record, "context")
            self.assertEqual(log_record.context, first_record.context)


class TestInputDriver(TestCase):
    def test_iterates_eagerly(self) -> None:
        click_event = dummy_click_event("test", None)
        expected_calls = random.randint(2, 10)
        expected_messages = [f"processed input {click_event}"] * expected_calls
        iter_mock = MagicMock()
        iter_mock.__iter__.return_value = repeat(click_event, expected_calls)

        with self.assertLogs(logger, logging.DEBUG) as logged:
            input_driver = InputDriver(iter_mock)
            input_driver.start()
            input_driver.join(timeout=1.0)

        self.assertEqual(list(iter_mock), [], "expected iterator to be exhausted")
        self.assertEqual([r.message for r in logged.records], expected_messages)


if __name__ == "__main__":
    main()
