import pytest

from swaystatus.config import Config, decode_element_key
from swaystatus.element import BaseElement


def test_decode_element_key() -> None:
    """Ensure that element key is parsed."""
    assert decode_element_key("foo") == ("foo", None)
    assert decode_element_key("foo:") == ("foo", "")
    assert decode_element_key("foo:a") == ("foo", "a")
    assert decode_element_key("foo:a:b") == ("foo", "a:b")


def test_decode_element_key_no_name() -> None:
    """Ensure that an element key contains the name."""
    with pytest.raises(AssertionError):
        decode_element_key("")
        decode_element_key(":")
        decode_element_key(":a")
        decode_element_key(":a:b")


def test_config_element_singleton(monkeypatch) -> None:
    """Ensure that elements with the same key map to the same instance."""

    # For this test, it's only important that the element class returned is
    # valid, not unique to the name. The only question is whether or not the
    # same instance is returned for the same key.

    class Element(BaseElement):
        pass

    def element_class(config: Config, name: str) -> type[BaseElement]:
        return Element

    monkeypatch.setattr(Config, "element_class", element_class)

    config = Config()

    assert config.element("foo") is config.element("foo")
    assert config.element("foo") is not config.element("bar")
    assert config.element("foo") is not config.element("foo:a")
    assert config.element("foo:a") is config.element("foo:a")
    assert config.element("foo:a") is not config.element("foo:b")
