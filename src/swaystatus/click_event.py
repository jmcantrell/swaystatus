"""A click event describes a block that was clicked by a pointer."""

from dataclasses import dataclass


@dataclass(slots=True, kw_only=True, frozen=True)
class ClickEvent:
    """
    Data class representing an event generated when clicking on a status bar block.

    Follows the event specification described in the CLICK EVENTS section of swaybar-protocol(7).
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

    def __str__(self) -> str:
        return f"click event button={self.button} name={self.name!r} instance={self.instance!r}"


__all__ = [ClickEvent.__name__]
