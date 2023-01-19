"""
Generate a status line for swaybar.

This package provides a simple and flexible framework to facilitate the
production of an interactive status line for swaybar.

There are two primary ways of interacting with this package:

1. Defining modules using the base class `swaystatus.element.BaseElement` to
   produce status bar blocks. For details, see the documentation for
   `swaystatus.element`.

2. Producing encoded content for swaybar with the `swaystatus` command. For
   details on the command line interface, run `swaystatus --help`. For details
   on configuring swaystatus, see the documentation for `swaystatus.config`.

This package does not contain any modules. It simply provides a way to make
them usable. One of the goals of this project is to be as unopinionated as
possible. I prefer simple, easy to read, modules, but you may want colorful,
feature-filled, eye candy. This package supports both, but provides neither.

This package does support the usage of external module packages, however,
making it easy to use any number of published module collections. For example,
I might have my modules published on PyPI as `my-awesome-swaystatus-modules`
and as long as that package has an entry point defined for
`swaystatus.modules`, it will be found by swaystatus and its modules available
to use.

Something like the following in the `pyproject.toml` for your modules package
should suffice:

    [project.entry-points."swaystatus.modules"]
    package = 'my_awesome_swaystatus_modules'
"""
