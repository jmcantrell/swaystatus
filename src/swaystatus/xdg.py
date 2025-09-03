import os
from pathlib import Path

cache_home = Path(os.environ.get("XDG_CACHE_HOME", "~/.cache")).expanduser()
config_home = Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser()
data_home = Path(os.environ.get("XDG_DATA_HOME", "~/.local/share")).expanduser()
state_home = Path(os.environ.get("XDG_STATE_HOME", "~/.local/state")).expanduser()
