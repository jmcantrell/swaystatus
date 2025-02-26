from typing import Iterator

from swaystatus import BaseElement, Block
from swaystatus.output import OutputGenerator


def test_output_multiple_blocks() -> None:
    """Ensure that a single element is able to output multiple blocks."""
    texts = ["foo", "bar", "baz"]

    class Element(BaseElement):
        name = "test"

        def blocks(self) -> Iterator[Block]:
            for text in texts:
                yield self.block(text)

    output = OutputGenerator([Element()])
    assert list(output.blocks()) == [Block(name="test", full_text=text) for text in texts]


def test_output_multiple_elements() -> None:
    """Ensure that multiple elements output their blocks in the correct order."""

    class Element1(BaseElement):
        name = "test1"

        def blocks(self) -> Iterator[Block]:
            yield self.block("foo")

    class Element2(BaseElement):
        name = "test2"

        def blocks(self) -> Iterator[Block]:
            yield self.block("bar")

    output = OutputGenerator([Element1(), Element2()])

    assert list(output.blocks()) == [
        Block(name="test1", full_text="foo"),
        Block(name="test2", full_text="bar"),
    ]
