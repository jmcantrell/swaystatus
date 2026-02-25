"""A block is a single unit of content for the status bar."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True, kw_only=True)
class Block:
    """
    Data class representing a unit of status bar content.

    Follows the block specification described in the BODY section of swaybar-protocol(7).
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
        return f"block full_text={self.full_text!r} name={self.name!r} instance={self.instance!r}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({', '.join(f'{k}={v!r}' for k, v in self.min_dict().items())})"

    def min_dict(self) -> dict[str, Any]:
        """Return a dict representation of the dataclass without any unset values."""
        return {field: value for field, value in asdict(self).items() if value is not None}


__all__ = [Block.__name__]
