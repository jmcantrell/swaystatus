"""
Framework for creating an interactive status line for swaybar.

Typical usage consists of the following:

    1. Create elements by subclassing `BaseElement` to produce blocks.
        - See `swaystatus.element` about creating elements.
        - See `swaystatus.modules` about where to put element modules.

    2. Configure swaystatus to use those elements.
        - See `swaystatus.config` about enabling and configuring elements.

    3. Produce content for swaybar with the `swaystatus` command.
        - See `swaystatus --help` for command line usage.
        - See `status_command` in sway-bar(5) to set the status command.

See swaybar-protocol(7) for a full description of the status bar protocol.
"""

import locale

from .block import Block
from .click_event import ClickEvent
from .element import BaseElement

# Locale is set to "C" by default.
locale.setlocale(locale.LC_ALL, "")

__all__ = [
    Block.__name__,
    ClickEvent.__name__,
    BaseElement.__name__,
]
