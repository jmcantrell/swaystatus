"""A click event describes a block that was clicked by a pointer."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True, kw_only=True)
class ClickEvent:
    """Data class for events generated when clicking on status bar blocks."""

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
        return f"click event button={self.button}"

    def as_dict(self) -> dict[str, Any]:
        """Return a dict representation of this instance without any unset values."""
        return {name: value for name, value in asdict(self).items() if value is not None}
