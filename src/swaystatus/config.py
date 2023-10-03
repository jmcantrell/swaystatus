"""
Configuring swaystatus to do your bidding.

Configuration is defined in a toml file. The first file that exists in the
following list (in order of preference) is used for configuration:

    1. The value of the command line option `--config-file`
    2. `$SWAYSTATUS_CONFIG_FILE`
    3. `<directory>/config.toml` where `<directory>` is the value of the
       command line option `--config-dir`
    4. `$SWAYSTATUS_CONFIG_DIR/config.toml`
    5. `$XDG_CONFIG_HOME/swaystatus/config.toml`
    6. `$HOME/.config/swaystatus/config.toml`

At the very minimum, this configuration file should contain the key to define
elements that will produce content blocks:

    order = ['hostname', 'clock']

If it's not obvious by the name of the key, it also defines the order that
elements will be displayed.

Each name in that list should correspond to a python file contained in a
modules package visible to swaystatus. For a modules package to be visible to
swaystatus, it must be one of the following:

    1. A python package path provided to the command line interface option
       `--include` (can be used multiple times).

    2. A python package called `modules` in the configuration directory. The
       first package that exists in the following list (in order of preference)
       will be visible:

          a. `<directory>/modules/` where `<directory>` is the value of the
             command line option `--config-dir`
          b. `$SWAYSTATUS_CONFIG_DIR/modules/`
          c. `$XDG_CONFIG_HOME/swaystatus/modules/`
          d. `$HOME/.config/swaystatus/modules/`

    3. A python package path specified in the configuration file:

        include = ['/path/to/modules1', '/path/to/modules2']

    4. A python package path specified in an environment variable:

        SWAYSTATUS_MODULE_PATH=/path/to/modules1:/path/to/modules2

    5. An installed python package with an entry point for `swaystatus.modules`
       defined like the following in your `pyproject.toml` (obviously your
       package name will be different):

          [project.entry-points."swaystatus.modules"]
          package = "my_awesome_swaystatus_modules"

Any combination of the above methods can be used. Packages are searched for
modules in the order of preference defined above. If any packages contain
modules with the same name, the first package that provides it will be used.

The following keys are recognized in the configuration file:

    - `order`: A list of module names to use in the status bar. It also defines
      the order in which they will be displayed. Modules can be included more
      than once. Modules can also be defined with an instance name, like
      `module:foo`, which can have their own settings (see the example below).

    - `interval`: A float that dictates how often the status bar will be
      updated (in seconds, default: 1.0).

    - `click_events`: A boolean that dictates whether or not click events will
      be sent to swaystatus by swaybar over stdin (default: true).

    - `include`: A list of directory paths to python packages that will be
      included when searching for module files.

    - `env`: A dictionary that defines environment variables that will be
      available to any click handler shell commands. This can be defined at the
      top level, for a module, or for a specific instance of a module.

    - `on_click`: A dictionary that maps pointer device button numbers to shell
      commands. The commands can be defined as either a single string or a list
      of strings. This can be defined at the top level, for a module, or for a
      specific instance of a module.

    - `settings`: A dictionary that maps module names to dictionaries that will
      be passed to the element's initializer as keyword arguments.

If any key is missing, it's default will be used. The `order` key isn't even
required, but to see anything in the status bar, it should contain at least one
module.

For example, the configuration file might look like:

    order = [
        'hostname',
        'path_exists:/mnt/foo',
        'memory',
        'clock',
        'clock:work'
    ]

    [env]
    terminal = 'foot'

    [settings.hostname]
    full_text = "host: {}"

    [settings.path_exists]
    on_click.1 = '$terminal --working-directory="$instance"'
    on_click.2 = '$terminal --hold df $instance'

    [settings."clock:work".env]
    TZ = 'Asia/Tokyo'
"""


config = {
    "order": [],
    "interval": 1.0,
    "click_events": True,
    "include": [],
    "env": {},
    "on_click": {},
    "settings": {},
}
