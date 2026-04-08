import os
from pathlib import Path


def path_normalized(value: os.PathLike[str] | str) -> Path:
    return Path(value).expanduser().resolve()
