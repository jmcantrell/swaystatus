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
        self.assertEqual(
            str(Block(full_text="foo", name="test")),
            "block full_text='foo' name='test' instance=None",
        )
        self.assertEqual(
            str(Block(full_text="foo", name="test", instance="a")),
            "block full_text='foo' name='test' instance='a'",
        )

    def test_repr(self) -> None:
        self.assertEqual(
            repr(Block(full_text="foo", name="test")),
            "Block(full_text='foo', name='test')",
        )

    def test_min_dict(self) -> None:
        dummy_block_params = list(asdict(dummy_block).items())
        expected_dict = dict(
            random.sample(
                dummy_block_params,
                k=random.randint(1, len(dummy_block_params) // 2),
            )
        )
        self.assertEqual(Block(**expected_dict).min_dict(), expected_dict)


if __name__ == "__main__":
    main()
