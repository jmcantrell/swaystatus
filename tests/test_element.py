import random
from pathlib import Path
from subprocess import Popen
from typing import Any, Iterator

from pytest import mark, raises
from pytest_mock import MockerFixture

from swaystatus.block import Block
from swaystatus.click_event import ClickEvent
from swaystatus.element import BaseElement, ElementRegistry, ShellCommand, UpdateHandler


class TestElement:
    def test_blocks_must_be_implemented(self) -> None:
        """Test that the blocks method must be implemented."""
        with raises(NotImplementedError):
            BaseElement().blocks()

        class Element(BaseElement):
            name = "test"

            def blocks(self) -> Iterator[Block]:
                yield self.block("foo")

        assert next(Element().blocks()) == Block(name="test", full_text="foo")

    def test_block_spawn(self) -> None:
        """Test that the block method returns a block tied to its element."""

        class Element(BaseElement):
            name = "test"

        element = Element()
        assert element.block("foo") == Block(full_text="foo", name="test")
        assert element.block("foo", instance="a") == Block(full_text="foo", name="test", instance="a")
        assert Element(instance="a").block("bar") == Block(full_text="bar", name="test", instance="a")

    def test_block_refuses_instance_override(self, dummy_click_event):
        """Test that the block method tries to prevent instance mismatches."""

        class Element(BaseElement):
            name = "test"

        with raises(ValueError):
            Element(instance="a").block("bar", instance="b")

    def test_click_handler_missing(self, dummy_click_event) -> None:
        """Test that a click event with no handler is ignored."""
        assert_update_is(BaseElement().on_click(dummy_click_event), False)

    def test_click_handler_method(self, mocker: MockerFixture, dummy_click_event) -> None:
        """Test that a click handler can be defined as a method."""

        class Element(BaseElement):
            def on_click_1(self, click_event: ClickEvent) -> None:
                pass

        element = Element()
        spy = mocker.spy(element, "on_click_1")
        assert_update_is(element.on_click(dummy_click_event), False)
        spy.assert_called_once_with(dummy_click_event)

    def test_click_handler_init_function(self, mocker: MockerFixture, dummy_click_event) -> None:
        """Test that a click handler function can be set at initialization."""
        click_handler = mocker.Mock(return_value=None)
        element = BaseElement(on_click={dummy_click_event.button: click_handler})
        assert_update_is(element.on_click(dummy_click_event), False)
        click_handler.assert_called_once_with(element, dummy_click_event)

    def test_click_handler_init_shell_command(self, tmp_path, dummy_click_event) -> None:
        """Test that a click handler shell command can be set at initialization."""
        marker_file = tmp_path / "test"
        shell_command = f"touch {marker_file}"
        element = BaseElement(on_click={dummy_click_event.button: shell_command})
        assert_update_handler_result_is(element.on_click(dummy_click_event), True)
        assert marker_file.is_file(), f"expected file to exist: {marker_file}"

    def test_click_handler_init_shell_command_env(self, tmp_path, dummy_string, dummy_click_event) -> None:
        """Test that a click handler shell command can use environment variables."""
        text = dummy_string(random.randint(10, 30))
        env = {"foo": text}
        output_file = tmp_path / "output"
        shell_command = f"echo ~ $foo $button >{output_file}"
        expected_output = f"{Path.home()} {text} {dummy_click_event.button}"
        element = BaseElement(on_click={dummy_click_event.button: shell_command}, env=env)
        assert_update_handler_result_is(element.on_click(dummy_click_event), True)
        assert output_file.read_text().strip() == expected_output, "unexpected shell command output"

    @mark.parametrize("update", map(bool, range(2)))
    def test_click_handler_result_update(self, update, dummy_click_event) -> None:
        """Test that a click handler can request a status update."""

        class Element(BaseElement):
            def on_click_1(self, *args) -> bool:
                return update

        assert_update_is(Element().on_click(dummy_click_event), update)

    @mark.parametrize("update", map(bool, range(2)))
    def test_click_handler_result_update_handler(self, update, dummy_click_event) -> None:
        """Test that a click handler can request a deferred status update."""

        def update_handler_inner() -> bool:
            return update

        class Element(BaseElement):
            def on_click_1(self, *args) -> UpdateHandler:
                return update_handler_inner

        assert_update_handler_result_is(Element().on_click(dummy_click_event), update)

    @mark.parametrize(
        ["command", "update"],
        [
            ("true", True),
            ("false", False),
        ],
    )
    def test_click_handler_result_process(self, command: ShellCommand, update: bool, dummy_click_event) -> None:
        """Test that a successful process will trigger a status update."""

        class Element(BaseElement):
            def on_click_1(self, *args) -> Popen:
                return Popen(command)

        assert_update_handler_result_is(Element().on_click(dummy_click_event), update)

    @mark.parametrize(
        ("command", "update"),
        [
            ("true", True),
            (["true"], True),
            ("false", False),
            (["false"], False),
        ],
    )
    def test_click_handler_result_shell_command(self, command: ShellCommand, update: bool, dummy_click_event) -> None:
        """Test that a shell command can trigger a status update."""

        class Element(BaseElement):
            def on_click_1(self, *args) -> ShellCommand:
                return command

        assert_update_handler_result_is(Element().on_click(dummy_click_event), update)


def assert_update_is(actual: Any, expected: bool) -> None:
    assert isinstance(actual, bool)
    assert actual is expected, f"expected update to be {expected}"


def assert_update_handler_result_is(handler: Any, update: bool) -> None:
    assert callable(handler), "expected update handler to be a function"
    assert_update_is(handler(), update)


class TestElementRegistry:
    def setup_method(self) -> None:
        class Element1(BaseElement):
            name = "test1"

        class Element2(BaseElement):
            name = "test2"

        self.element1 = Element1()
        self.element1a = Element1(instance="a")
        self.element1b = Element1(instance="b")
        self.element2a = Element2(instance="a")
        self.element2b = Element2(instance="b")
        self.element_registry = ElementRegistry(
            [
                self.element1,
                self.element1a,
                self.element1b,
                self.element2a,
                self.element2b,
            ]
        )

    def test_get(self) -> None:
        """Test that an element can be retrieved by name."""
        self.assert_get_is("test1", None, self.element1)
        self.assert_get_raises("bogus", None)

    def test_get_instance(self) -> None:
        """Test that an element can be retrieved by name and instance."""
        self.assert_get_is("test1", "a", self.element1a)
        self.assert_get_is("test1", "b", self.element1b)
        self.assert_get_raises("test2", "c")
        self.assert_get_raises("bogus", "a")

    def test_get_instance_fallback(self) -> None:
        """Test that requesting an element instance falls back to one with the same name."""
        self.assert_get_is("test1", "c", self.element1)
        self.assert_get_raises("test2", None)

    def get(self, name: str, instance: str | None = None) -> BaseElement:
        return self.element_registry.get(name, instance)

    def assert_get_is(self, name: str, instance: str | None, element: BaseElement) -> None:
        assert self.get(name, instance) is element, f"expected getting {name=} and {instance=} to return {element}"

    def assert_get_raises(self, name: str, instance: str | None) -> None:
        with raises(KeyError):
            self.get(name, instance)
