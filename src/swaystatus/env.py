import os
import sys
from pathlib import Path

bin_name = os.path.basename(sys.argv[0])
config_home = Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser()


def environ_path(name: str) -> Path | None:
    if value := os.environ.get(name):
        return Path(value).expanduser()
    return None


def environ_paths(name: str) -> list[Path] | None:
    if value := os.environ.get(name):
        return [Path(p).expanduser() for p in value.split(":")]
    return None
