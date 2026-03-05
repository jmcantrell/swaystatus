from pytest import raises

from swaystatus.config import decode_element_key


class TestDecodeElementKey:
    def test_no_instance(self) -> None:
        """Test that a key with a name and no instance can be parsed."""
        assert decode_element_key("foo") == ("foo", None)
        assert decode_element_key("foo:") == ("foo", None)

    def test_instance(self) -> None:
        """Test that a key with a name and an instance can be parsed."""
        assert decode_element_key("foo:a") == ("foo", "a")
        assert decode_element_key("foo:a:b") == ("foo", "a:b")

    def test_name_required(self) -> None:
        """Test that a key must contain a name."""
        with raises(ValueError):
            decode_element_key("")
            decode_element_key(":")
            decode_element_key(":a")
            decode_element_key(":a:b")
