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


def test_element_on_click_str_kwarg(capfd):
    button = 1

    expected = {
        "${foo}": "some string",  # manually added variable
        "${button}": str(button),  # environment variables (including event)
        "~": str(Path.home()),  # shell tilde expansion
    }

    for orig, result in expected.items():
        BaseElement(
            on_click={1: f"echo {orig}"}, env={"foo": "some string"}
        ).on_click({"button": button})
        captured = capfd.readouterr()
        assert captured.out.strip() == result


def test_element_create_block_default():
    assert BaseElement().create_block("test") == {"full_text": "test"}


def test_element_create_block_with_name():
    element = BaseElement()
    element.name = "foo"
    assert element.create_block("test") == {
        "full_text": "test",
        "name": element.name,
    }


def test_element_create_block_with_kwargs():
    kwargs = {"foo": "a", "bar": "b"}
    assert BaseElement().create_block("test", **kwargs) == dict(
        full_text="test", **kwargs
    )


def test_element_on_interval_default():
    assert BaseElement().on_interval() is None
