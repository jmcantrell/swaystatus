import shutil
from pathlib import Path
from typing import Callable

import pytest

from swaystatus.dataclasses import ClickEvent


@pytest.fixture
def fake_click_event() -> Callable[[], ClickEvent]:
    default_kwargs = dict(
        x=0,
        y=0,
        button=0,
        event=0,
        relative_x=0,
        relative_y=0,
        width=0,
        height=0,
        scale=0.0,
    )

    def create(**kwargs) -> ClickEvent:
        return ClickEvent(**default_kwargs | kwargs)

    return create


@pytest.fixture
def temp_module(tmp_path):
    def copy(src_name: str | None = None, dst_name: str | None = None) -> Path:
        src = Path(__file__).parent / "modules" / (src_name or "no_output.py")
        dst = tmp_path / (dst_name or src.name)
        dst.parent.mkdir(parents=True, exist_ok=True)
        (dst.parent / "__init__.py").touch()
        shutil.copyfile(src, dst)
        return dst

    return copy
