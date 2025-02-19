from swaystatus.element import BaseElement
from swaystatus.updater import Updater


def test_updater_no_blocks():
    """Ensure that if an element does not emit any blocks, none appear in the output."""

    class NoBlocks(BaseElement):
        def on_update(self, output):
            pass

    updater = Updater(NoBlocks())

    assert updater.update() == []


def test_updater_multiple_blocks():
    """Ensure that a single element is able to output multiple blocks."""

    texts = ["foo", "bar", "baz"]

    class MultipleBlocks(BaseElement):
        def on_update(self, output):
            output.extend([self.create_block(text) for text in texts])

    updater = Updater(MultipleBlocks())

    assert updater.update() == [dict(full_text=text) for text in texts]


def test_updater_multiple_elements():
    """Ensure that multiple elements output their blocks in the correct order."""

    class Foo(BaseElement):
        def on_update(self, output):
            output.append(self.create_block("foo"))

    class Bar(BaseElement):
        def on_update(self, output):
            output.append(self.create_block("bar"))

    updater = Updater(Foo(), Bar())

    assert updater.update() == [dict(full_text="foo"), dict(full_text="bar")]
