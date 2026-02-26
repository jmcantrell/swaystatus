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
