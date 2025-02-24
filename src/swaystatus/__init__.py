"""
Framework for creating interactive an status line for swaybar.

There are two primary ways of using this package:

1. Defining modules by subclassing `swaystatus.BaseElement` to produce status
   bar blocks. For details, see the documentation for `swaystatus.element`.

2. Producing content for swaybar with the `swaystatus` command. For details on
   the command line interface, run `swaystatus --help`. For details on
   configuring swaystatus, see the documentation for `swaystatus.config`.

This package does not contain any element modules. The intention is to provide
a simple implementation of the swaybar-protocol(7) and leave the details to the
user.

There is support the usage of external module packages, making it easy to use
any number of local or published module collections. For example, there might
be modules published on PyPI as `awesome-swaystatus-modules` and as long as
that package has an entry point defined for `swaystatus.modules`, it will be
found by swaystatus and its modules available to use after installing.

Something like the following in the `pyproject.toml` is all that's necessary:

    [project.entry-points."swaystatus.modules"]
    package = 'awesome_swaystatus_modules'
"""

__all__ = ["Block", "ClickEvent", "BaseElement"]

from .block import Block
from .click_event import ClickEvent
from .element import BaseElement
