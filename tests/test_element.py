from dataclasses import replace
from pathlib import Path
from random import randint
from subprocess import Popen

import pytest

from swaystatus import BaseElement, ClickEvent
from swaystatus.element import ClickHandlerResult, ShellCommand

from .fake import click_event


def test_base_element_blocks_not_implemented() -> None:
    """Ensure that the block generator is implemented on subclasses."""
    with pytest.raises(NotImplementedError):
        BaseElement().blocks()


def test_element_on_click_method() -> None:
    """Ensure that handlers can be defined as a method."""
    actual_button: int | None = None
    expected_button = randint(1, 3)

    class Element(BaseElement):
        def register_click(self, button: int) -> None:
            nonlocal actual_button
            actual_button = button

        def on_click_1(self, event: ClickEvent):
            self.register_click(1)

        def on_click_2(self, event: ClickEvent):
            self.register_click(2)

        def on_click_3(self, event: ClickEvent):
            self.register_click(3)

    element = Element()
    element.on_click(replace(click_event, button=expected_button))
    assert expected_button == actual_button


def test_element_on_click_function() -> None:
    """Ensure that function handlers can be set at initialization."""

    class Element(BaseElement):
        name = "test"

    clicked_element: BaseElement | None = None

    def handler(element: BaseElement, event: ClickEvent):
        nonlocal clicked_element
        clicked_element = element

    button = randint(1, 5)
    element = Element(on_click={button: handler})
    element.on_click(replace(click_event, button=button))
    assert clicked_element is element


def test_element_on_click_shell_command(tmp_path) -> None:
    """Ensure that shell command handlers can be set at initialization."""

    class Element(BaseElement):
        name = "test"

    button = randint(1, 5)
    cases = {
        "$foo": "some string",  # environment variables added
        "${button}": str(button),  # environment variables from event
        "~": str(Path.home()),  # shell tilde expansion
    }
    env = {"foo": cases["$foo"]}
    event = replace(click_event, button=button)
    stdout_file = tmp_path / "stdout"
    for s, expected_output in cases.items():
        handler = f"echo {s} >{stdout_file}"  # shell redirection
        element = Element(on_click={button: handler}, env=env)
        process = element.on_click(event)
        assert isinstance(process, Popen)
        process.wait()
        actual_output = stdout_file.read_text().strip()
        assert actual_output == expected_output


def test_element_on_click_function_return_passthrough() -> None:
    """Ensure that a function handler's return value is preserved sometimes."""

    class Element(BaseElement):
        name = "test"

    for expected_value in (None, False, True, lambda: True, Popen("true")):

        def handler(element: BaseElement, event: ClickEvent) -> ClickHandlerResult:
            return expected_value

        button = randint(1, 5)
        element = Element(on_click={button: handler})
        actual_value = element.on_click(replace(click_event, button=button))
        assert actual_value is expected_value


def test_element_on_click_function_return_shell_command_run() -> None:
    """Ensure that a function handler's return value is run if it's a shell command."""

    class Element(BaseElement):
        name = "test"

    for expected_args in ("true", ["true"]):

        def handler(element: BaseElement, event: ClickEvent) -> ShellCommand:
            return expected_args

        button = randint(1, 5)
        element = Element(on_click={button: handler})
        process = element.on_click(replace(click_event, button=button))
        assert isinstance(process, Popen)
        assert process.args is expected_args
