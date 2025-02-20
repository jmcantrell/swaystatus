from typing import Any

from .element import BaseElement

type Output = list[dict[str, Any]]


class Updater:
    def __init__(self, *elements: BaseElement) -> None:
        super().__init__()
        self.elements = list(elements)

    def update(self) -> Output:
        """
        Prompt every element for any updates to the status bar.

        It does this by giving each element a turn at appending blocks to an
        `output` list that it passes as the first argument to the element's
        `on_update` method. This is done in the order that the elements were
        given to the updater at initialization.
        """
        output: Output = []
        for element in self.elements:
            element.on_update(output)
        return output
