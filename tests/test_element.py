import random
from pathlib import Path
from string import ascii_letters
from subprocess import Popen
from typing import Iterator

from pytest import fail, mark, raises
from pytest_mock import MockerFixture

from swaystatus.block import Block
from swaystatus.click_event import ClickEvent
from swaystatus.element import BaseElement, ShellCommand, UpdateHandler


class TestElement:
    def test_blocks_must_be_implemented(self) -> None:
        """The blocks method must be implemented."""
        with raises(NotImplementedError):
            BaseElement("clock").blocks()

        class Element(BaseElement):
            def blocks(self) -> Iterator[Block]:
                yield self.block("foo")

        assert next(Element("clock").blocks()) == Block(name="clock", full_text="foo")

    def test_block_spawn(self) -> None:
        """The block method returns a block tied to its element."""
        assert BaseElement("clock").block("foo") == Block(full_text="foo", name="clock")
        assert BaseElement("clock", "a").block("bar") == Block(full_text="bar", name="clock", instance="a")

    def test_click_handler_missing(self, dummy_click_event) -> None:
        """A click event with no handler is ignored."""
        assert BaseElement("clock").on_click(dummy_click_event) is False

    def test_click_handler_method(self, mocker: MockerFixture, dummy_click_event) -> None:
        """A click handler can be defined as a method."""

        class Element(BaseElement):
            def on_click_1(self, click_event: ClickEvent) -> None:
                pass

        element = Element("clock")
        spy = mocker.spy(element, "on_click_1")
        assert element.on_click(dummy_click_event) is False
        spy.assert_called_once_with(dummy_click_event)

    def test_click_handler_init_none(self, dummy_click_event) -> None:
        """A click handler can be disabled at initialization."""

        class Element(BaseElement):
            def on_click_1(self, click_event: ClickEvent) -> None:
                fail("expected click handler to not be called")

        element = Element("clock", on_click={dummy_click_event.button: None})
        assert element.on_click(dummy_click_event) is False

    def test_click_handler_init_function(self, mocker: MockerFixture, dummy_click_event) -> None:
        """A click handler function can be set at initialization."""
        click_handler = mocker.Mock(return_value=None)
        element = BaseElement("clock", on_click={dummy_click_event.button: click_handler})
        assert element.on_click(dummy_click_event) is False
        click_handler.assert_called_once_with(element, dummy_click_event)

    def test_click_handler_init_command(self, tmp_path, dummy_click_event) -> None:
        """A click handler shell command can be set at initialization."""
        marker_file = tmp_path / "test"
        command = f"touch {marker_file}"
        element = BaseElement("clock", on_click={dummy_click_event.button: command})
        assert element.on_click(dummy_click_event) is True
        assert marker_file.is_file(), f"expected file to exist: {marker_file}"

    def test_click_handler_init_command_env(self, tmp_path, dummy_string, dummy_click_event) -> None:
        """A click handler shell command can use environment variables."""
        text = "".join(random.choices(ascii_letters, k=random.randint(10, 30)))
        env = {"foo": text}
        output_file = tmp_path / "output"
        command = f"echo ~ $foo $button >{output_file}"
        expected_output = f"{Path.home()} {text} {dummy_click_event.button}"
        element = BaseElement("clock", on_click={dummy_click_event.button: command}, env=env)
        assert element.on_click(dummy_click_event) is True
        assert output_file.read_text().strip() == expected_output, "unexpected shell command output"

    @mark.parametrize("update", map(bool, range(2)))
    def test_click_handler_result_update(self, update, dummy_click_event) -> None:
        """A click handler can request a status update."""

        class Element(BaseElement):
            def on_click_1(self, *args) -> bool:
                return update

        assert Element("clock").on_click(dummy_click_event) is update

    @mark.parametrize("update", map(bool, range(2)))
    def test_click_handler_result_update_handler(self, update, dummy_click_event) -> None:
        """A click handler can request a deferred status update."""

        def update_handler_inner() -> bool:
            return update

        class Element(BaseElement):
            def on_click_1(self, *args) -> UpdateHandler:
                return update_handler_inner

        assert Element("clock").on_click(dummy_click_event) is update

    @mark.parametrize(
        ["command", "update"],
        [
            ("true", True),
            ("false", False),
        ],
    )
    def test_click_handler_result_process(self, command: ShellCommand, update: bool, dummy_click_event) -> None:
        """A successful process will trigger a status update."""

        class Element(BaseElement):
            def on_click_1(self, *args) -> Popen:
                return Popen(command)

        assert Element("clock").on_click(dummy_click_event) is update

    @mark.parametrize(
        ("command", "update"),
        [
            ("true", True),
            (["true"], True),
            ("false", False),
            (["false"], False),
        ],
    )
    def test_click_handler_result_command(self, command: ShellCommand, update: bool, dummy_click_event) -> None:
        """A shell command can trigger a status update."""

        class Element(BaseElement):
            def on_click_1(self, *args) -> ShellCommand:
                return command

        assert Element("clock").on_click(dummy_click_event) is update
