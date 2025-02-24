"""A click event describes a block that was click by a pointer."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True, kw_only=True)
class ClickEvent:
    """
    Data class that maps directly on to the JSON representation.

    See the "CLICK EVENTS" section of swaybar-protocol(7) for a full description.
    """

    name: str | None = None
    instance: str | None = None
    x: int
    y: int
    button: int
    event: int
    relative_x: int
    relative_y: int
    width: int
    height: int
    scale: float

    def dict(self) -> dict[str, Any]:
        return {name: value for name, value in asdict(self).items() if value is not None}
