import dataclasses

from swaystatus.click_event import ClickEvent

fake_block_kwargs = dict(
    full_text="full",
    short_text="short",
    color="#eeeeee",
    background="#ffffff",
    border="#000000",
    border_top=1,
    border_bottom=2,
    border_left=3,
    border_right=4,
    min_width=100,
    align="center",
    name="foo",
    instance="bar",
    urgent=False,
    separator=",",
    separator_block_width=2,
    markup="pango",
)

empty_click_event = ClickEvent(
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


def fake_click_event(**kwargs) -> ClickEvent:
    return dataclasses.replace(empty_click_event, **kwargs)
