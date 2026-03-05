import random
from dataclasses import asdict

from swaystatus.block import Block


def test_block_as_dict(dummy_block) -> None:
    """Test that only set attributes are included when exporting as a dictionary."""
    dummy_block_kwargs = list(asdict(dummy_block).items())
    kwargs = dict(
        random.sample(
            dummy_block_kwargs,
            k=random.randint(1, len(dummy_block_kwargs)),
        )
    )
    assert Block(**kwargs).as_dict() == kwargs
