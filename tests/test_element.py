import dataclasses
import logging
import random
from pathlib import Path
from string import ascii_letters
from subprocess import Popen
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from unittest.mock import Mock, patch

from swaystatus.block import Block
from swaystatus.click_event import ClickEvent
from swaystatus.element import BaseElement, ShellCommand, UpdateHandler
from swaystatus.logger import logger

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


def random_string(min_length: int, max_length: int) -> str:
    return "".join(random.choices(ascii_letters, k=random.randint(min_length, max_length)))


class TestElement(TestCase):
    def test_str(self) -> None:
        self.assertEqual(
            str(BaseElement(name="test")),
            "element name='test' instance=None",
        )
        self.assertEqual(
            str(BaseElement(name="test", instance="a")),
            "element name='test' instance='a'",
        )

    def test_blocks_must_be_implemented(self) -> None:
        with self.assertRaises(NotImplementedError):
            BaseElement("clock").blocks()

    def test_block_spawn(self) -> None:
        self.assertEqual(
            BaseElement("clock").block("tick"),
            Block(full_text="tick", name="clock"),
        )
        self.assertEqual(
            BaseElement("clock", "a").block("tick"),
            Block(full_text="tick", name="clock", instance="a"),
        )

    def test_click_handler_missing(self) -> None:
        self.assertFalse(BaseElement("clock").on_click(dummy_click_event))

    def test_click_handler_method(self) -> None:
        class Element(BaseElement):
            def on_click_1(self, click_event: ClickEvent) -> None:
                pass

        element = Element("clock")
        with patch.object(element, "on_click_1", wraps=element.on_click_1) as mock:
            self.assertFalse(element.on_click(dummy_click_event))
            mock.assert_called_once_with(dummy_click_event)

    def test_click_handler_init_none(self) -> None:
        class Element(BaseElement):
            def on_click_1(self, click_event: ClickEvent) -> None:
                click_mock()

        click_mock = Mock()
        element = Element("clock", on_click={dummy_click_event.button: None})
        self.assertFalse(element.on_click(dummy_click_event))
        click_mock.assert_not_called()

    def test_click_handler_init_function(self) -> None:
        click_handler = Mock(return_value=None)
        element = BaseElement("clock", on_click={dummy_click_event.button: click_handler})
        self.assertFalse(element.on_click(dummy_click_event))
        click_handler.assert_called_once_with(element, dummy_click_event)

    def test_click_handler_init_command(self) -> None:
        with TemporaryDirectory() as temp_dir:
            marker_file = Path(temp_dir) / "test"
            command = f"touch {marker_file}"
            element = BaseElement("clock", on_click={dummy_click_event.button: command})
            update_handler = element.on_click(dummy_click_event)
            assert callable(update_handler)
            self.assertTrue(update_handler())
            self.assertTrue(marker_file.is_file())

    def test_click_handler_init_command_env(self) -> None:
        text = random_string(10, 30)
        with TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "output"
            command = f"echo ~ $foo $button >{output_file}"
            expected_output = f"{Path.home()} {text} {dummy_click_event.button}"
            element = BaseElement("clock", env={"foo": text}, on_click={dummy_click_event.button: command})
            update_handler = element.on_click(dummy_click_event)
            assert callable(update_handler)
            self.assertTrue(update_handler())
            self.assertEqual(output_file.read_text().strip(), expected_output)

    def test_click_handler_result_update(self) -> None:
        class Element(BaseElement):
            def on_click_1(self, *args) -> bool:
                return update

        for update in [False, True]:
            with self.subTest(update=update):
                self.assertEqual(Element("clock").on_click(dummy_click_event), update)

    def test_click_handler_result_update_handler(self) -> None:
        def update_handler_inner() -> bool:
            return update

        class Element(BaseElement):
            def on_click_1(self, *args) -> UpdateHandler:
                return update_handler_inner

        for update in [False, True]:
            with self.subTest(update=update):
                update_handler = Element("clock").on_click(dummy_click_event)
                assert callable(update_handler)
                self.assertEqual(update_handler(), update)

    def test_click_handler_result_process(self) -> None:
        class Element(BaseElement):
            def on_click_1(self, *args) -> Popen:
                return Popen(command)

        for command, update in [
            ("true", True),
            ("false", False),
        ]:
            with self.subTest(command=command, update=update):
                update_handler = Element("clock").on_click(dummy_click_event)
                assert callable(update_handler)
                self.assertEqual(update_handler(), update)

    def test_click_handler_result_command(self) -> None:
        class Element(BaseElement):
            def on_click_1(self, *args) -> ShellCommand:
                return command

        for command, update in [
            ("true", True),
            (["true"], True),
            ("false", False),
            (["false"], False),
        ]:
            with self.subTest(command=command, update=update):
                update_handler = Element("clock").on_click(dummy_click_event)
                assert callable(update_handler)
                self.assertEqual(update_handler(), update)

    def test_click_handler_result_command_logged(self) -> None:
        class Element(BaseElement):
            def on_click_1(self, *args) -> ShellCommand:
                return command

        element = Element("clock")
        command = "echo line1; echo BOOM >&2; echo line2; echo BANG >&2"

        with self.assertLogs(logger, logging.DEBUG) as logged:
            update_handler = element.on_click(dummy_click_event)
            assert callable(update_handler)
            self.assertTrue(update_handler())

        debug = [r.message for r in logged.records if r.levelno == logging.DEBUG]
        error = [r.message for r in logged.records if r.levelno == logging.ERROR]

        self.assertEqual(
            debug,
            [
                f"click handler method {element.on_click_1!r}",
                f"click handler environment {dataclasses.asdict(dummy_click_event)!r}",
                f"click handler result {command!r}",
                "line1",
                "line2",
            ],
        )
        self.assertEqual(error, ["BOOM", "BANG"])


if __name__ == "__main__":
    main()
