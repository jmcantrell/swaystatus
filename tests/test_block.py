from typing import Any, Mapping
from unittest import TestCase, main

from swaystatus.block import Block
from tests.fake import fake_block_kwargs


class TestBlock(TestCase):
    def test_as_dict(self) -> None:
        """Test that only set attributes are included when exporting as a dictionary."""
        kwarg_pairs = list(fake_block_kwargs.items())
        for n in range(len(kwarg_pairs)):
            with self.subTest(n=n):
                kwargs: Mapping[str, Any] = dict(kwarg_pairs[:n])
                assert Block(**kwargs).as_dict() == kwargs


if __name__ == "__main__":
    main()
