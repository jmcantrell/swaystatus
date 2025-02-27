import json
import shutil
from io import StringIO
from pathlib import Path
from typing import IO, Iterable

import pytest

from swaystatus import ClickEvent


@pytest.fixture
def tmp_module(tmp_path):
    def copy(src_name: str | None = None, dst_name: str | None = None) -> Path:
        """Copy a test module to a package directory."""
        src = Path(__file__).parent / "modules" / (src_name or "no_output.py")
        dst = tmp_path / (dst_name or src.name)
        dst.parent.mkdir(parents=True, exist_ok=True)
        (dst.parent / "__init__.py").touch()
        shutil.copyfile(src, dst)
        return dst

    return copy


@pytest.fixture
def click_events_file():
    def creator(events: Iterable[ClickEvent]) -> IO[str]:
        file = StringIO()
        file.write("[\n")
        for event in events:
            file.write(f",{json.dumps(event.as_dict())}\n")
        file.seek(0)
        return file

    return creator
