from dataclasses import replace
from pathlib import Path

import pytest

from swaystatus import BaseElement

from .fake import click_event


def test_base_element_blocks_not_implemented():
    """Ensure that nothing is added to the output by default."""
    with pytest.raises(NotImplementedError):
        BaseElement().blocks()


def test_element_on_click_method():
    """Ensure that click event handlers can be defined as a method."""
    hit = False

    class Element(BaseElement):
        def on_click_1(self, event):
            nonlocal hit
            hit = True

    Element().on_click(replace(click_event, button=1))
    assert hit


def test_element_on_click_function():
    """Ensure that function click event handlers can be set at initialization."""
    hit = False

    class Element(BaseElement):
        name = "test"

    def handler(event):
        nonlocal hit
        hit = True

    Element(on_click={1: handler}).on_click(replace(click_event, button=1))
    assert hit


def test_element_on_click_shell_command(tmp_path):
    """Ensure that shell command click event handlers can be set at initialization."""
    button = 1
    cases = {
        "${foo}": "some string",  # environment variables added
        "${button}": str(button),  # environment variables from event
        "~": str(Path.home()),  # shell tilde expansion
    }
    env = {"foo": cases["${foo}"]}
    event = replace(click_event, button=button)
    tmp_path.mkdir(parents=True, exist_ok=True)
    stdout_file = tmp_path / "stdout"

    class Element(BaseElement):
        name = "test"

    for s, expected in cases.items():
        handler = f"echo {s} >{stdout_file}"  # shell redirection
        Element(on_click={1: handler}, env=env).on_click(event)
        assert stdout_file.read_text().strip() == expected
