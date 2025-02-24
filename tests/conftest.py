import json
import shutil
from io import StringIO
from pathlib import Path
from typing import Iterable

import pytest

from swaystatus import ClickEvent


@pytest.fixture
def tmp_module(tmp_path):
    def copy(name: str) -> Path:
        """Copy a test module to a package directory."""
        src = Path(__file__).parent / "modules" / f"{name}.py"
        dst = tmp_path / src.name
        (tmp_path / "__init__.py").touch()
        shutil.copyfile(src, dst)
        return dst

    return copy


@pytest.fixture
def click_events_file():
    def creator(events: Iterable[ClickEvent]):
        file = StringIO()
        file.write("[\n")
        for event in events:
            file.write(f",{json.dumps(event.dict())}\n")
        file.seek(0)
        return file

    return creator
