from typing import Iterator

from swaystatus.dataclasses import Block
from swaystatus.element import BaseElement


class Element(BaseElement):
    def blocks(self) -> Iterator[Block]:
        yield from []
