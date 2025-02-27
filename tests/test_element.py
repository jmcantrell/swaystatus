from dataclasses import replace
from pathlib import Path

import pytest

from swaystatus import BaseElement, ClickEvent

from .fake import click_event


def test_base_element_blocks_not_implemented() -> None:
    """Ensure that the block generator is implemented on subclasses."""
    with pytest.raises(NotImplementedError):
        BaseElement().blocks()


def test_element_on_click_subclass() -> None:
    """Ensure that click event handlers can be defined as a method."""
    was_clicked = False

    class Element(BaseElement):
        def on_click_1(self, event: ClickEvent):
            nonlocal was_clicked
            was_clicked = True

    element = Element()
    element.on_click(replace(click_event, button=1))
    assert was_clicked


def test_element_on_click_function() -> None:
    """Ensure that function click event handlers can be set at initialization."""

    class Element(BaseElement):
        name = "test"

    clicked_element: BaseElement | None = None

    def handler(element: BaseElement, event: ClickEvent):
        nonlocal clicked_element
        clicked_element = element

    element = Element(on_click={1: handler})
    element.on_click(replace(click_event, button=1))
    assert clicked_element is element


def test_element_on_click_shell_command(tmp_path) -> None:
    """Ensure that shell command click event handlers can be set at initialization."""
    button = 1
    cases = {
        "${foo}": "some string",  # environment variables added
        "${button}": str(button),  # environment variables from event
        "~": str(Path.home()),  # shell tilde expansion
    }
    env = {"foo": cases["${foo}"]}
    event = replace(click_event, button=button)
    stdout_file = tmp_path / "stdout"

    class Element(BaseElement):
        name = "test"

    for s, expected_output in cases.items():
        handler = f"echo {s} >{stdout_file}"  # shell redirection
        element = Element(on_click={1: handler}, env=env)
        process = element.on_click(event)
        assert process
        process.wait()
        actual_output = stdout_file.read_text().strip()
        assert actual_output == expected_output
