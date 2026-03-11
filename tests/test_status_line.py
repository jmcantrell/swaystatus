from typing import Iterator
from unittest import TestCase, main

from swaystatus.block import Block
from swaystatus.element import BaseElement
from swaystatus.status_line import StatusLine


class TestStatusLine(TestCase):
    def test_blocks_multiple_elements(self) -> None:

        class Element1(BaseElement):
            def blocks(self) -> Iterator[Block]:
                yield self.block("foo")

        class Element2(BaseElement):
            def blocks(self) -> Iterator[Block]:
                yield self.block("bar")

        self.assertEqual(
            StatusLine(
                [
                    Element1("test1"),
                    Element2("test2"),
                ]
            ).blocks(),
            [
                Block(name="test1", full_text="foo"),
                Block(name="test2", full_text="bar"),
            ],
        )

    def test_blocks_multiple_per_element(self) -> None:
        texts = ["foo", "bar", "baz"]

        class Element(BaseElement):
            def blocks(self) -> Iterator[Block]:
                yield from map(self.block, texts)

        self.assertEqual(
            StatusLine([Element("test")]).blocks(),
            [Block(name="test", full_text=text) for text in texts],
        )

    def test_click_target_exact(self) -> None:
        for name, instance in [("clock", None), ("clock", "home")]:
            with self.subTest(name=name, instance=instance):
                element = BaseElement(name, instance)
                self.assertIs(StatusLine([element]).click_target(name, instance), element)

    def test_click_target_fallback(self) -> None:
        element = BaseElement("clock", None)
        element_var = BaseElement("clock", "home")
        self.assertIs(StatusLine([element, element_var]).click_target("clock", "work"), element)

    def test_click_target_raises(self) -> None:
        with self.assertRaises(KeyError):
            StatusLine([]).click_target("clock")
        with self.assertRaises(KeyError):
            StatusLine([]).click_target("clock", "home")


if __name__ == "__main__":
    main()
