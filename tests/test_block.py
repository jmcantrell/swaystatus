import random
from dataclasses import asdict
from unittest import TestCase, main

from swaystatus.block import Block

dummy_block = Block(
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
    name="clock",
    instance="home",
    urgent=False,
    separator=False,
    separator_block_width=2,
    markup="pango",
)


class TestBlock(TestCase):
    def test_str(self) -> None:
        self.assertEqual(str(dummy_block), "block full_text='full'")

    def test_as_dict(self) -> None:
        dummy_block_kwargs = list(asdict(dummy_block).items())
        expected_kwargs = dict(
            random.sample(
                dummy_block_kwargs,
                k=random.randint(1, len(dummy_block_kwargs)),
            )
        )
        actual_kwargs = Block(**expected_kwargs).as_dict()
        self.assertEqual(actual_kwargs, expected_kwargs)


if __name__ == "__main__":
    main()
