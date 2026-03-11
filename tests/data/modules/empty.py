from typing import Iterator

from swaystatus import BaseElement, Block


class Element(BaseElement):
    def blocks(self) -> Iterator[Block]:
        yield from []
