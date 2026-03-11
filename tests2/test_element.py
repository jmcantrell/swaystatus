import random
from pathlib import Path
from string import ascii_letters
from subprocess import Popen
from tempfile import TemporaryDirectory
from typing import Iterator
from unittest import TestCase
from unittest.mock import Mock, patch

from pytest import fail, raises

from swaystatus.block import Block
from swaystatus.click_event import ClickEvent
from swaystatus.element import BaseElement, ShellCommand, UpdateHandler

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


class TestElement(TestCase):
    def test_blocks_must_be_implemented(self) -> None:
        with raises(NotImplementedError):
            BaseElement("clock").blocks()

        class Element(BaseElement):
            def blocks(self) -> Iterator[Block]:
                yield self.block("foo")

        self.assertEqual(next(Element("clock").blocks()), Block(name="clock", full_text="foo"))

    def test_block_spawn(self) -> None:
        self.assertEqual(BaseElement("clock").block("foo"), Block(full_text="foo", name="clock"))
        self.assertEqual(BaseElement("clock", "a").block("bar"), Block(full_text="bar", name="clock", instance="a"))

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
                fail("expected click handler to not be called")

        element = Element("clock", on_click={dummy_click_event.button: None})
        self.assertFalse(element.on_click(dummy_click_event))

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
            self.assertTrue(element.on_click(dummy_click_event))
            self.assertTrue(marker_file.is_file(), f"expected file to exist: {marker_file}")

    def test_click_handler_init_command_env(self) -> None:
        text = "".join(random.choices(ascii_letters, k=random.randint(10, 30)))
        with TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "output"
            command = f"echo ~ $foo $button >{output_file}"
            expected_output = f"{Path.home()} {text} {dummy_click_event.button}"
            element = BaseElement("clock", on_click={dummy_click_event.button: command}, env={"foo": text})
            self.assertTrue(element.on_click(dummy_click_event))
            self.assertEqual(output_file.read_text().strip(), expected_output, "unexpected shell command output")

    def test_click_handler_result_update(self) -> None:
        for update in [False, True]:
            with self.subTest(update=update):

                class Element(BaseElement):
                    def on_click_1(self, *args) -> bool:
                        return update

                self.assertIs(Element("clock").on_click(dummy_click_event), update)

    def test_click_handler_result_update_handler(self) -> None:
        for update in [False, True]:
            with self.subTest(update=update):

                def update_handler_inner() -> bool:
                    return update

                class Element(BaseElement):
                    def on_click_1(self, *args) -> UpdateHandler:
                        return update_handler_inner

                self.assertIs(Element("clock").on_click(dummy_click_event), update)

    def test_click_handler_result_process(self) -> None:

        class Element(BaseElement):
            def on_click_1(self, *args) -> Popen:
                return Popen(command)

        cases = [
            ("true", True),
            ("false", False),
        ]

        for command, update in cases:
            with self.subTest(command=command, update=update):
                self.assertIs(Element("clock").on_click(dummy_click_event), update)

    def test_click_handler_result_command(self) -> None:

        class Element(BaseElement):
            def on_click_1(self, *args) -> ShellCommand:
                return command

        cases = [
            ("true", True),
            (["true"], True),
            ("false", False),
            (["false"], False),
        ]

        for command, update in cases:
            with self.subTest(command=command, update=update):
                self.assertIs(Element("clock").on_click(dummy_click_event), update)
