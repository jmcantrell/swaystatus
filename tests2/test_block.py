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
    def test_as_dict_no_none(self) -> None:
        dummy_block_kwargs = list(asdict(dummy_block).items())
        kwargs = dict(
            random.sample(
                dummy_block_kwargs,
                k=random.randint(1, len(dummy_block_kwargs)),
            )
        )
        self.assertEqual(Block(**kwargs).as_dict(), kwargs)


if __name__ == "__main__":
    main()
