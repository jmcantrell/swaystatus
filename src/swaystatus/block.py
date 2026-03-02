"""A block is a single unit of content for the status bar."""

from dataclasses import dataclass
from typing import Any

from .dataclasses import min_dict, min_repr


@dataclass(slots=True, kw_only=True)
class Block:
    """
    Data class representing a unit of status bar content.

    Follows the block specification described in the BODY section of
    swaybar-protocol(7).
    """

    full_text: str | None = None
    short_text: str | None = None
    color: str | None = None
    background: str | None = None
    border: str | None = None
    border_top: int | None = None
    border_bottom: int | None = None
    border_left: int | None = None
    border_right: int | None = None
    min_width: int | str | None = None
    align: str | None = None
    name: str | None = None
    instance: str | None = None
    urgent: bool | None = None
    separator: bool | None = None
    separator_block_width: int | None = None
    markup: str | None = None

    def __str__(self) -> str:
        return f"block full_text={self.full_text!r}"

    def __repr__(self) -> str:
        return min_repr(self)

    def as_dict(self) -> dict[str, Any]:
        return min_dict(self)


__all__ = [Block.__name__]
