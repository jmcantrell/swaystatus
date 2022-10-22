from pathlib import Path
from swaystatus import BaseElement


def test_base_element_udpate_default():
    output = []
    BaseElement().on_update(output)
    assert len(output) == 0


def test_element_on_click_no_handler():
    BaseElement().on_click({"button": 1})


def test_element_on_click_method():
    hit = False

    class Element(BaseElement):
        def on_click_1(self, event):
            nonlocal hit
            hit = True

    Element().on_click({"button": 1})

    assert hit


def test_element_on_click_callable_kwarg():
    hit = False

    def handler(event):
        nonlocal hit
        hit = True

    BaseElement(on_click={1: handler}).on_click({"button": 1})

    assert hit


def test_element_on_click_str_kwarg(tmp_path):
    button = 1

    cases = {
        "${foo}": "some string",  # environment variables added
        "${button}": str(button),  # environment variables from event
        "~": str(Path.home()),  # shell tilde expansion
    }

    env = {"foo": cases["${foo}"]}
    event = {"button": button}

    tmp_path.mkdir(exist_ok=True)
    stdout_file = tmp_path / "stdout"

    for s, expected in cases.items():
        handler = f"echo {s} >{stdout_file}"  # shell redirection
        BaseElement(on_click={1: handler}, env=env).on_click(event).wait()
        assert stdout_file.read_text().strip() == expected


def test_element_create_block_default():
    assert BaseElement().create_block("test") == {"full_text": "test"}


def test_element_create_block_with_id():
    element = BaseElement(name="foo", instance="bar")
    assert element.create_block("test") == {
        "full_text": "test",
        "name": element.name,
        "instance": element.instance,
    }


def test_element_create_block_with_id_set_after_init():
    element = BaseElement()
    element.name = "foo"
    element.instance = "bar"
    assert element.create_block("test") == {
        "full_text": "test",
        "name": element.name,
        "instance": element.instance,
    }


def test_element_create_block_with_id_set_in_block():
    element = BaseElement(name="foo", instance="bar")
    assert element.create_block("test", name="baz", instance="qux") == {
        "full_text": "test",
        "name": "baz",
        "instance": "qux",
    }


def test_element_create_block_with_kwargs():
    kwargs = {"foo": "a", "bar": "b"}
    assert BaseElement().create_block("test", **kwargs) == dict(full_text="test", **kwargs)


def test_element_on_interval_default():
    assert BaseElement().on_interval() is None
