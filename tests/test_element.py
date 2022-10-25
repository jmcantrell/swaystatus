from pathlib import Path
from swaystatus.element import BaseElement


def test_element_udpate_no_output():
    """
    Ensure that nothing is added to the output by default.
    """

    output = []
    BaseElement().on_update(output)
    assert len(output) == 0


def test_element_on_click_method():
    """
    Ensure that click event handlers can be defined as a method.
    """

    hit = False

    class Element(BaseElement):
        def on_click_1(self, event):
            nonlocal hit
            hit = True

    Element().on_click({"button": 1})

    assert hit


def test_element_on_click_function():
    """
    Ensure that function click event handlers can be set at initialization.
    """

    hit = False

    def handler(event):
        nonlocal hit
        hit = True

    BaseElement(on_click={1: handler}).on_click({"button": 1})

    assert hit


def test_element_on_click_shell(tmp_path):
    """
    Ensure that shell command click event handlers can be set at
    initialization.
    """

    button = 1

    cases = {
        "${foo}": "some string",  # environment variables added
        "${button}": str(button),  # environment variables from event
        "~": str(Path.home()),  # shell tilde expansion
    }

    env = {"foo": cases["${foo}"]}
    event = {"button": button}

    tmp_path.mkdir(parents=True, exist_ok=True)
    stdout_file = tmp_path / "stdout"

    for s, expected in cases.items():
        handler = f"echo {s} >{stdout_file}"  # shell redirection
        BaseElement(on_click={1: handler}, env=env).on_click(event).wait()
        assert stdout_file.read_text().strip() == expected


def test_element_create_block_default():
    """
    Ensure that when no name or instance is set, it's not included in the
    output.
    """

    assert BaseElement().create_block("test") == {"full_text": "test"}


def test_element_create_block_with_id_set_at_init():
    """
    Ensure that name and instance can be set at initialization.
    """

    element = BaseElement(name="foo", instance="bar")
    assert element.create_block("test") == {
        "full_text": "test",
        "name": element.name,
        "instance": element.instance,
    }


def test_element_create_block_with_id_set_after_init():
    """
    Ensure that name and instance can be overridden after initialization.
    """

    element = BaseElement()
    element.name = "foo"
    element.instance = "bar"
    assert element.create_block("test") == {
        "full_text": "test",
        "name": element.name,
        "instance": element.instance,
    }


def test_element_create_block_with_id_set_in_block():
    """
    Ensure that name and instance can be overridden per-block.
    """

    element = BaseElement(name="foo", instance="bar")
    assert element.create_block("test", name="baz", instance="qux") == {
        "full_text": "test",
        "name": "baz",
        "instance": "qux",
    }


def test_element_create_block_with_kwargs():
    """
    Ensure that keyword arguments passed to `create_block` are included in the
    result.
    """

    kwargs = {"foo": "a", "bar": "b"}
    assert BaseElement().create_block("test", **kwargs) == dict(
        full_text="test", **kwargs
    )
