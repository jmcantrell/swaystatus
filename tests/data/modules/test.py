from collections.abc import Iterator

from swaystatus import BaseElement, Block


class Element(BaseElement):
    def blocks(self) -> Iterator[Block]:
        yield self.block("test")
