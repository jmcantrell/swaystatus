def test_click_event_as_dict(dummy_click_event) -> None:
    """Test that certain unset keys are not included when exporting as a dictionary."""
    exported = dummy_click_event.as_dict()
    assert "name" in exported
    assert "instance" in exported
    dummy_click_event.name = None
    dummy_click_event.instance = None
    exported = dummy_click_event.as_dict()
    assert "name" not in exported
    assert "instance" not in exported
