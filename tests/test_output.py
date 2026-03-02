import json
import random
from io import StringIO
from signal import SIGCONT, SIGSTOP
from typing import Iterator
from unittest import TestCase, main

from swaystatus.block import Block
from swaystatus.element import BaseElement
from swaystatus.output import OutputProcessor, status_line


class TestStatusLine(TestCase):
    def test_blocks_multiple_elements(self) -> None:
        """Test that multiple elements output their blocks in the correct order."""

        class Element1(BaseElement):
            name = "test1"

            def blocks(self) -> Iterator[Block]:
                yield self.block("foo")

        class Element2(BaseElement):
            name = "test2"

            def blocks(self) -> Iterator[Block]:
                yield self.block("bar")

        actual_blocks = list(status_line([Element1(), Element2()]))
        expected_blocks = [
            Block(name="test1", full_text="foo"),
            Block(name="test2", full_text="bar"),
        ]
        self.assertListEqual(actual_blocks, expected_blocks)

    def test_blocks_multiple_blocks_per_element(self) -> None:
        """Test that a single element is able to output multiple blocks."""
        texts = ["foo", "bar", "baz"]

        class Element(BaseElement):
            name = "test"

            def blocks(self) -> Iterator[Block]:
                yield from map(self.block, texts)

        actual_blocks = list(status_line([Element()]))
        expected_blocks = [Block(name="test", full_text=text) for text in texts]
        self.assertListEqual(actual_blocks, expected_blocks)


class TestOutputProcessor(TestCase):
    def test_header_click_events(self) -> None:
        """Test that the click events setting is reflected in the output header."""
        for click_events in [None, False, True]:
            with self.subTest(click_events=click_events):
                output_processor = OutputProcessor([], click_events=click_events)
                assert output_processor.header["click_events"] == bool(click_events)

    def test_process_encoded(self) -> None:
        """Test that output is written in the expected format."""

        class Element(BaseElement):
            name = "test"
            count = 0

            def blocks(self) -> Iterator[Block]:
                self.count += 1
                yield self.block(f"iteration {self.count}")

        output_file = StringIO()
        output_processor = OutputProcessor([Element()])
        status_lines = output_processor.process(output_file)

        def next_iteration() -> tuple[list[Block], list[str]]:
            pos = output_file.tell()
            status_line = next(status_lines)
            output_file.seek(pos)
            output_lines = output_file.readlines()
            return status_line, output_lines

        def block(i: int) -> Block:
            return Block(full_text=f"iteration {i}", name="test")

        def body_line(i: int) -> str:
            return f",[{json.dumps(dict(full_text=f'iteration {i}', name='test'))}]\n"

        status_line, output_lines = next_iteration()
        assert len(output_lines) == 3
        assert status_line == [block(1)]
        header = json.loads(output_lines[0])
        assert header["version"] == 1
        assert header["stop_signal"] == SIGSTOP
        assert header["cont_signal"] == SIGCONT
        assert not header["click_events"]
        assert output_lines[1] == "[[]\n"  # start of infinite body array
        assert output_lines[2] == body_line(1)
        for i in range(2, random.randint(5, 10)):
            status_line, output_lines = next_iteration()
            assert status_line == [block(i)]
            assert output_lines == [body_line(i)]


if __name__ == "__main__":
    main()
