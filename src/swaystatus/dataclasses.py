from dataclasses import asdict
from typing import Any


def min_dict(obj: Any) -> dict[str, Any]:
    """Return a dict representation of the dataclass without any unset values."""
    return {name: value for name, value in asdict(obj).items() if value is not None}
