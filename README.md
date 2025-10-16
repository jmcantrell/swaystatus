# swaystatus

Generate a status line for [swaybar][swaybar-protocol].

## Installation

### Python

Install as a python package:

    pip install swaystatus

### Arch User Repository (AUR)

There are two packages available for Arch Linux, available via the AUR:

- [swaystatus][pkg-aur] (stable, based on the latest tag)
- [swaystatus-git][pkg-aur-git] (unstable, based on the latest commit)

## Usage

To see documentation for the python package:

    pydoc swaystatus

To see documentation for the command line interface:

    swaystatus --help

See [sway-bar(5)][sway-bar] for details on setting `status_command`.

See [swaybar-protocol(7)][swaybar-protocol] for a definition of the status bar protocol.

[pkg-aur]: https://aur.archlinux.org/packages/swaystatus/
[pkg-aur-git]: https://aur.archlinux.org/packages/swaystatus-git/
[sway-bar]: https://man.archlinux.org/man/extra/sway/sway-bar.5.en
[swaybar-protocol]: https://man.archlinux.org/man/swaybar-protocol.7
