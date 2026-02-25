import itertools
import json
import logging
import random
from collections.abc import Iterator, Sequence
from io import StringIO
from signal import SIGCONT, SIGSTOP
from string import ascii_letters
from threading import Barrier
from unittest import TestCase, main
from unittest.mock import patch

from swaystatus.block import Block
from swaystatus.element import BaseElement
from swaystatus.logger import logger
from swaystatus.output import OutputDriver, OutputProcessor


class TestOutputProcessor(TestCase):
    def setUp(self) -> None:
        self.stdout = StringIO()
        stdout_patcher = patch("sys.stdout", self.stdout)
        stdout_patcher.start()
        self.addCleanup(stdout_patcher.stop)

    def test_header_click_events(self) -> None:
        for click_events in [False, True]:
            with self.subTest(click_events=click_events):
                output_processor = OutputProcessor([], click_events)
                self.assertEqual(output_processor.header["click_events"], bool(click_events))

    def test_status_line_multiple_elements(self) -> None:
        num_elements = random.randint(2, 5)
        element_names = ascii_letters[:num_elements]

        class Element(BaseElement):
            def blocks(self) -> Iterator[Block]:
                yield self.block(f"element {self.name}")

        elements = list(map(Element, element_names))
        self.assertEqual(
            list(OutputProcessor(elements, False).status_line()),
            [Block(full_text=f"element {n}", name=n) for n in element_names],
        )

    def test_status_line_multiple_per_element(self) -> None:
        num_blocks = random.randint(2, 5)
        block_names = ascii_letters[:num_blocks]

        class Element(BaseElement):
            def blocks(self) -> Iterator[Block]:
                for name in block_names:
                    yield self.block(f"block {name}")

        elements = [Element("test")]
        self.assertEqual(
            list(OutputProcessor(elements, False).status_line()),
            [Block(full_text=f"block {n}", name="test") for n in block_names],
        )

    def test_iter_encoded(self) -> None:
        iteration = itertools.count(0)

        class Element(BaseElement):
            def blocks(self) -> Iterator[Block]:
                yield self.block(f"i={next(iteration)}")

        processed = iter(OutputProcessor([Element("clock")], False))

        def next_iteration() -> tuple[Sequence[Block], list[str]]:
            pos = self.stdout.tell()
            blocks = next(processed)
            self.stdout.seek(pos)
            output_lines = self.stdout.readlines()
            return blocks, output_lines

        def block_ith(i: int) -> Block:
            return Block(full_text=f"i={i}", name="clock")

        def body_line_ith(i: int) -> str:
            return f",[{json.dumps(block_ith(i).min_dict())}]\n"

        blocks, output_lines = next_iteration()

        self.assertEqual(len(output_lines), 3)
        self.assertEqual(blocks, [block_ith(0)])
        self.assertEqual(
            json.loads(output_lines[0]),
            {
                "version": 1,
                "stop_signal": SIGSTOP,
                "cont_signal": SIGCONT,
                "click_events": False,
            },
        )

        self.assertEqual(output_lines[1], "[[]\n")
        self.assertEqual(output_lines[2], body_line_ith(0))
        for i in range(1, random.randint(5, 10)):
            blocks, output_lines = next_iteration()
            self.assertEqual(blocks, [block_ith(i)])
            self.assertEqual(output_lines, [body_line_ith(i)])


class TestOutputDriver(TestCase):
    def test_iterate_on_tick(self) -> None:
        yield_acquire = Barrier(2, timeout=1.0)
        block = Block(full_text="test")
        expected_calls = random.randint(2, 10)
        expected_messages = ["processed 1 output block(s)"] * expected_calls

        def fake_status_lines() -> Iterator[Sequence[Block]]:
            while True:
                yield_acquire.wait()
                yield [block]

        with self.assertLogs(logger, logging.DEBUG) as logged:
            output_driver = OutputDriver(fake_status_lines(), None)
            output_driver.start()
            for _ in range(expected_calls):
                output_driver.next()
                yield_acquire.wait()
            output_driver.stop()
            output_driver.join(timeout=1.0)

        self.assertFalse(output_driver.is_alive(), "output driver never died")
        self.assertEqual([r.message for r in logged.records], expected_messages)


if __name__ == "__main__":
    main()
