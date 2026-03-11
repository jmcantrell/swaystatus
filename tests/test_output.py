import itertools
import json
import random
from io import StringIO
from signal import SIGCONT, SIGSTOP
from typing import Iterator, Sequence

from pytest import mark

from swaystatus.block import Block
from swaystatus.element import BaseElement
from swaystatus.output import OutputProcessor
from swaystatus.status_line import StatusLine


class TestOutputProcessor:
    @mark.parametrize("click_events", [None, False, True])
    def test_header_click_events(self, click_events) -> None:
        """The click events setting is reflected in the output header."""
        stats_line = StatusLine([])
        output_processor = OutputProcessor(StringIO(), stats_line, click_events)
        assert output_processor.header["click_events"] == bool(click_events)

    def test_iter_encoded(self) -> None:
        """Output is written in the expected format."""

        iteration = itertools.count(1)

        class Element(BaseElement):
            def blocks(self) -> Iterator[Block]:
                yield self.block(f"iteration {next(iteration)}")

        output_file = StringIO()
        status_line = StatusLine([Element("test")])
        processor = iter(OutputProcessor(output_file, status_line, False))

        def next_iteration() -> tuple[Sequence[Block], list[str]]:
            pos = output_file.tell()
            blocks = next(processor)
            output_file.seek(pos)
            output_lines = output_file.readlines()
            return blocks, output_lines

        def block(i: int) -> Block:
            return Block(full_text=f"iteration {i}", name="test")

        def body_line(i: int) -> str:
            return f",[{json.dumps(dict(full_text=f'iteration {i}', name='test'))}]\n"

        blocks, output_lines = next_iteration()
        assert len(output_lines) == 3
        assert blocks == [block(1)]
        header = json.loads(output_lines[0])
        assert header["version"] == 1
        assert header["stop_signal"] == SIGSTOP
        assert header["cont_signal"] == SIGCONT
        assert not header["click_events"]
        assert output_lines[1] == "[[]\n"  # start of infinite body array
        assert output_lines[2] == body_line(1)
        for i in range(2, random.randint(5, 10)):
            blocks, output_lines = next_iteration()
            assert blocks == [block(i)]
            assert output_lines == [body_line(i)]
