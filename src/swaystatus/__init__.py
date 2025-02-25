"""
Framework for creating interactive an status line for swaybar.

There are two primary ways of using this package:

1. Defining modules by subclassing `swaystatus.BaseElement` to produce status
   bar blocks. For details, see the documentation for `swaystatus.element`.

2. Producing content for swaybar with the `swaystatus` command. For details on
   the command line interface, run `swaystatus --help`.

This package does not contain any element modules, but it does support the
usage of external module packages, making it easy to use any number of local or
published module collections.

See the documentation for `swaystatus.config` for details on adding modules and
configuration.

See swaybar-protocol(7) for a full description of the status bar protocol.
"""

__all__ = ["Block", "ClickEvent", "BaseElement"]

from .block import Block
from .click_event import ClickEvent
from .element import BaseElement
