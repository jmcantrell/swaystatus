import itertools
import json
import random
from io import StringIO
from signal import SIGCONT, SIGSTOP
from threading import Barrier
from typing import Iterator, Sequence
from unittest import TestCase, main

from swaystatus.block import Block
from swaystatus.element import BaseElement
from swaystatus.output import OutputDriver, OutputProcessor
from swaystatus.status_line import StatusLine


class TestOutputProcessor(TestCase):
    def test_header_click_events(self) -> None:
        for click_events in [False, True]:
            with self.subTest(click_events=click_events):
                output_processor = OutputProcessor(StringIO(), StatusLine([]), click_events)
                self.assertEqual(output_processor.header["click_events"], bool(click_events))

    def test_iter_encoded(self) -> None:
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
        self.assertEqual(len(output_lines), 3)
        self.assertEqual(blocks, [block(1)])
        self.assertEqual(
            json.loads(output_lines[0]),
            dict(
                version=1,
                stop_signal=SIGSTOP,
                cont_signal=SIGCONT,
                click_events=False,
            ),
        )
        self.assertEqual(output_lines[1], "[[]\n")
        self.assertEqual(output_lines[2], body_line(1))
        for i in range(2, random.randint(5, 10)):
            blocks, output_lines = next_iteration()
            self.assertEqual(blocks, [block(i)])
            self.assertEqual(output_lines, [body_line(i)])


class TestOutputDriver(TestCase):
    def test_iterate_on_tick(self) -> None:
        yield_acquire = Barrier(2, timeout=1.0)

        def fake_status_lines() -> Iterator[Sequence[Block]]:
            while True:
                yield_acquire.wait()
                yield []

        output_driver = OutputDriver(fake_status_lines(), None)
        output_driver.start()
        for _ in range(random.randint(2, 10)):
            output_driver.next()
            yield_acquire.wait()
        output_driver.stop()
        output_driver.join(timeout=1.0)
        self.assertFalse(output_driver.is_alive(), "output driver never died")


if __name__ == "__main__":
    main()
