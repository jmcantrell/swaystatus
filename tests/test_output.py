import json
import random
from io import StringIO
from signal import SIGCONT, SIGSTOP
from typing import Iterator

from swaystatus import BaseElement, Block
from swaystatus.output import OutputDelegator


def test_output_multiple_blocks() -> None:
    """Ensure that a single element is able to output multiple blocks."""
    texts = ["foo", "bar", "baz"]

    class Element(BaseElement):
        name = "test"

        def blocks(self) -> Iterator[Block]:
            for text in texts:
                yield self.block(text)

    output_delegator = OutputDelegator([Element()])
    actual_blocks = list(output_delegator.blocks())
    expected_blocks = [Block(name="test", full_text=text) for text in texts]
    assert actual_blocks == expected_blocks


def test_output_multiple_elements() -> None:
    """Ensure that multiple elements output their blocks in the correct order."""

    class Element1(BaseElement):
        name = "test1"

        def blocks(self) -> Iterator[Block]:
            yield self.block("foo")

    class Element2(BaseElement):
        name = "test2"

        def blocks(self) -> Iterator[Block]:
            yield self.block("bar")

    output_delegator = OutputDelegator([Element1(), Element2()])
    actual_blocks = list(output_delegator.blocks())
    expected_blocks = [
        Block(name="test1", full_text="foo"),
        Block(name="test2", full_text="bar"),
    ]
    assert actual_blocks == expected_blocks


def test_output_identical_elements_cached() -> None:
    """Ensure that identical elements are only polled once per iteration."""

    class Element(BaseElement):
        name = "test"
        count = 0

        def blocks(self) -> Iterator[Block]:
            self.count += 1
            yield self.block(str(self.count))

    element = Element()

    # Show that separate polls produce different blocks.
    assert list(element.blocks()) != list(element.blocks())

    output_delegator = OutputDelegator([element, element])

    # Show that the blocks produced by the element are reused.
    blocks_first = list(output_delegator.blocks())
    assert blocks_first[0] == blocks_first[1]

    # Show that the blocks produced by the last call are not reused.
    blocks_second = list(output_delegator.blocks())
    assert blocks_first != blocks_second


def test_output_process() -> None:
    """Ensure that output is written in the expected format."""

    class Element(BaseElement):
        name = "test"
        count = 0

        def blocks(self) -> Iterator[Block]:
            self.count += 1
            yield self.block(f"iteration {self.count}")

    output_file = StringIO()
    output_delegator = OutputDelegator([Element()])
    status = output_delegator.process(output_file)

    def next_iteration() -> tuple[list[Block], list[str]]:
        pos = output_file.tell()
        blocks = next(status)
        output_file.seek(pos)
        lines = output_file.readlines()
        return blocks, lines

    def block(i: int) -> Block:
        return Block(full_text=f"iteration {i}", name="test")

    def body_line(i: int) -> str:
        return f",[{json.dumps(dict(full_text=f'iteration {i}', name='test'))}]\n"

    blocks, lines = next_iteration()
    assert len(lines) == 3
    assert blocks == [block(1)]
    header = json.loads(lines[0])
    assert header["version"] == 1
    assert header["stop_signal"] == SIGSTOP
    assert header["cont_signal"] == SIGCONT
    assert not header["click_events"]
    assert lines[1] == "[[]\n"  # start of infinite body array
    assert lines[2] == body_line(1)
    for i in range(2, random.randint(5, 10)):
        blocks, lines = next_iteration()
        assert blocks == [block(i)]
        assert lines == [body_line(i)]


def test_output_process_header_click_events() -> None:
    """Ensure that click events setting is reflected in output header."""

    for click_events in [None, False, True]:
        kwargs = {}
        if click_events is not None:
            kwargs["click_events"] = click_events

        output_delegator = OutputDelegator([], click_events=click_events)

        file = StringIO()
        next(output_delegator.process(file))

        file.seek(0)
        header = json.loads(file.readline())

        assert header["click_events"] == bool(click_events)
