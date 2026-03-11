"""A status line is a sequence of content generating elements."""

from functools import cache, cached_property
from itertools import chain
from typing import Self, Sequence

from .block import Block
from .element import BaseElement


class StatusLine:
    """Container to hold elements used to generated output."""

    def __init__(self, elements: Sequence[BaseElement]) -> None:
        self.elements = elements

    def blocks(self) -> Sequence[Block]:
        return list(chain.from_iterable(element.blocks() for element in self.elements))

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> Sequence[Block]:
        return self.blocks()

    @cached_property
    def _element_lookup(self) -> dict[tuple[str, str | None], BaseElement]:
        return {(e.name, e.instance): e for e in self.elements}

    @cache
    def click_target(self, name: str, instance: str | None = None) -> BaseElement:
        """
        Return the element that should receive a click event.

        If a the click is targetting a specific element matching `instance` and
        an exact match is not found, look for an element with the same name but
        without an `instance`. Otherwise, raise `KeyError`.
        """
        if instance:
            try:
                return self._element_lookup[(name, instance)]
            except KeyError:
                pass
        return self._element_lookup[(name, None)]
