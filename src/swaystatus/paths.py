from pathlib import Path


def path_normalized(value: str) -> Path:
    return Path(value).expanduser().resolve()
