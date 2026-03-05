import logging
import random
from string import ascii_letters
from typing import Callable

from pytest import fixture

from swaystatus.block import Block
from swaystatus.click_event import ClickEvent


@fixture
def dummy_block() -> Block:
    return Block(
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
        separator=False,
        separator_block_width=2,
        markup="pango",
    )


@fixture
def dummy_click_event() -> ClickEvent:
    return ClickEvent(
        name="clock",
        instance="edt",
        x=1900,
        y=10,
        button=1,
        event=274,
        relative_x=100,
        relative_y=8,
        width=120,
        height=18,
        scale=0.0,
    )


@fixture
def dummy_string() -> Callable[[int], str]:
    def factory(length: int) -> str:
        return "".join(random.choices(ascii_letters, k=length))

    return factory


@fixture
def caplog_record(caplog) -> Callable[[int, str], logging.LogRecord | None]:
    def factory(levelno: int, text: str) -> logging.LogRecord | None:
        for record in caplog.records:
            if record.levelno == levelno and text in record.message:
                return record
        return None

    return factory


@fixture
def assert_log_record(caplog_record) -> Callable[[int, str], logging.LogRecord]:
    def factory(levelno: int, text: str) -> logging.LogRecord:
        log_record = caplog_record(levelno, text)
        assert log_record, f"expected {logging.getLevelName(levelno)} log record containing {text!r}"
        return log_record

    return factory
