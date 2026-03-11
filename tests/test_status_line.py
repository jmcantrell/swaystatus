from typing import Iterator

from pytest import mark, raises

from swaystatus.block import Block
from swaystatus.element import BaseElement
from swaystatus.status_line import StatusLine


class TestStatusLine:
    def test_blocks_multiple_elements(self) -> None:
        """Multiple elements output their blocks in the correct order."""

        class Element1(BaseElement):
            def blocks(self) -> Iterator[Block]:
                yield self.block("foo")

        class Element2(BaseElement):
            def blocks(self) -> Iterator[Block]:
                yield self.block("bar")

        actual_blocks = StatusLine([Element1("test1"), Element2("test2")]).blocks()
        expected_blocks = [
            Block(name="test1", full_text="foo"),
            Block(name="test2", full_text="bar"),
        ]
        assert actual_blocks == expected_blocks

    def test_blocks_multiple_per_element(self) -> None:
        """A single element is able to output multiple blocks."""
        texts = ["foo", "bar", "baz"]

        class Element(BaseElement):
            def blocks(self) -> Iterator[Block]:
                yield from map(self.block, texts)

        actual_blocks = StatusLine([Element("test")]).blocks()
        expected_blocks = [Block(name="test", full_text=text) for text in texts]
        assert actual_blocks == expected_blocks

    @mark.parametrize(["name", "instance"], [("clock", None), ("clock", "home")])
    def test_click_target_exact(self, name: str, instance: str | None) -> None:
        """An element that is an exact match can be retrieved."""
        element = BaseElement(name, instance)
        status_line = StatusLine([element])
        assert status_line.click_target(name, instance) is element

    def test_click_target_fallback(self) -> None:
        """A missing element with `instance` falls back to the same element without it."""
        element = BaseElement("clock", None)
        element_var = BaseElement("clock", "home")
        status_line = StatusLine([element, element_var])
        assert status_line.click_target("clock", "work") is element

    def test_click_target_raises(self) -> None:
        """An exception is raised if no element matches."""
        with raises(KeyError):
            StatusLine([]).click_target("clock")
        with raises(KeyError):
            StatusLine([]).click_target("clock", "home")
