"""A block is a unit of content for the status bar."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True, kw_only=True)
class Block:
    """Data class for units of status bar content."""

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

    def as_dict(self) -> dict[str, Any]:
        """Return a dict representation of this instance without any unset values."""
        return {name: value for name, value in asdict(self).items() if value is not None}
