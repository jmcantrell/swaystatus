import os
from pathlib import Path


def path_normalized(value: os.PathLike[str] | str) -> Path:
    """Return an absolute path with all symlinks resolved and user prefixes expanded."""
    return Path(value).expanduser().resolve()
