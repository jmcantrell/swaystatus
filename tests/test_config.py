from unittest import TestCase, main
from unittest.mock import patch

from swaystatus.config import Config, decode_element_key
from swaystatus.element import BaseElement


class TestConfig(TestCase):
    def setUp(self):
        self.patcher = patch("swaystatus.module.ModuleRegistry.get")
        self.patcher.start().return_value = BaseElement
        self.addCleanup(self.patcher.stop)
        self.config = Config()

    def test_same_name(self) -> None:
        """Test that identical keys return the same element."""
        self.assertIs(self.config.element("foo"), self.config.element("foo"))
        self.assertIs(self.config.element("foo:a"), self.config.element("foo:a"))

    def test_different_name(self) -> None:
        """Test that different keys return different elements."""
        self.assertIsNot(self.config.element("foo"), self.config.element("bar"))
        self.assertIsNot(self.config.element("foo:a"), self.config.element("foo:b"))


class TestDecodeElement(TestCase):
    def test_no_instance(self) -> None:
        """Test that a key with only a name is parsed."""
        self.assertEqual(decode_element_key("foo"), ("foo", None))

    def test_empty_instance(self) -> None:
        """Test that a key with an empty instance is parsed."""
        self.assertEqual(decode_element_key("foo:"), ("foo", ""))

    def test_instance(self) -> None:
        """Test that a key with an instance is parsed."""
        self.assertEqual(decode_element_key("foo:a"), ("foo", "a"))
        self.assertEqual(decode_element_key("foo:a:b"), ("foo", "a:b"))

    def test_name_required(self) -> None:
        """Test that a key must contain a name."""
        with self.assertRaises(ValueError):
            decode_element_key("")
            decode_element_key(":")
            decode_element_key(":a")
            decode_element_key(":a:b")


if __name__ == "__main__":
    main()
