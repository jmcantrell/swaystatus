import pytest
from swaystatus.element import BaseElement
from types import MethodType


def test_base_element_udpate():
    with pytest.raises(NotImplementedError):
        BaseElement().on_update([])


def test_element_click_no_handler():
    BaseElement().on_click({"button": 1})


@pytest.mark.parametrize("button", range(1, 6))
def test_element_click_handler(button):
    hit = False

    def handler(self, event):
        nonlocal hit
        hit = True

    element = BaseElement()
    setattr(element, f"on_click_{button}", MethodType(handler, element))

    element.on_click({"button": button})

    assert hit


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


def test_element_interval():
    assert BaseElement().on_interval() is None
