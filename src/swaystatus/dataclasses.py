from dataclasses import asdict
from typing import Any


def min_dict(obj: Any) -> dict[str, Any]:
    """Return a dict representation of the dataclass without any unset values."""
    return {name: value for name, value in asdict(obj).items() if value is not None}


def min_repr(obj: Any) -> str:
    """Return a python representation of the dataclass without any unset values."""
    return f"{type(obj).__name__}({', '.join(f'{k}={v!r}' for k, v in min_dict(obj).items())})"
