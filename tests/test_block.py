from typing import Any

from swaystatus import Block


def test_block_dict_minimal() -> None:
    """Ensure that only the keyword arguments passed are included in its `dict` form."""
    kwarg_pairs: list[tuple[str, Any]] = [
        ("full_text", "full"),
        ("short_text", "short"),
        ("color", "#eeeeee"),
        ("background", "#ffffff"),
        ("border", "#000000"),
        ("border_top", 1),
        ("border_bottom", 2),
        ("border_left", 3),
        ("border_right", 4),
        ("min_width", 100),
        ("align", "center"),
        ("name", "foo"),
        ("instance", "bar"),
        ("urgent", False),
        ("separator", ","),
        ("separator_block_width", 2),
        ("markup", "pango"),
    ]
    for i in range(len(kwarg_pairs)):
        kwargs = dict(kwarg_pairs[:i])
        assert Block(**kwargs).as_dict() == kwargs
