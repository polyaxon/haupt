import sys

from typing import List

from clipped.formatting import Printer

from haupt.managers.sandbox import SandboxConfigManager
from haupt.settings import set_sandbox_config
from polyaxon._cli.config import set_home_path
from polyaxon._cli.errors import handle_cli_error
from polyaxon._managers.home import HomeConfigManager


def show():
    """Show the current sandbox config."""
    _config = HomeConfigManager.get_config_or_default()
    Printer.heading(
        "In addition to environment variables, global configs will be loaded from:"
    )
    Printer.dict_tabulate(_config.to_dict())
    _config = SandboxConfigManager.get_config_or_default()
    Printer.heading("Sandbox config:")
    Printer.dict_tabulate(_config.to_dict())


def get(keys: List[str]):
    """Get the specific keys from the sandbox configuration."""
    _config = SandboxConfigManager.get_config_or_default()

    if not keys:
        return

    print_values = {}
    for key in keys:
        key = key.replace("-", "_")
        if hasattr(_config, key):
            print_values[key] = getattr(_config, key)
        else:
            Printer.print("Key `{}` is not recognised.".format(key))

    Printer.dict_tabulate(print_values)


def set(**kwargs):  # pylint:disable=redefined-builtin
    """Set the sandbox config values."""
    try:
        _config = SandboxConfigManager.get_config_or_default()
    except Exception as e:
        handle_cli_error(e, message="Load configuration.")
        Printer.heading("You can reset your config by running: `sandbox config-purge`")
        sys.exit(1)

    for key, value in kwargs.items():
        if value is not None:
            if key == "path":
                set_home_path(home_path=value)
            else:
                setattr(_config, key, value)

    set_sandbox_config(_config, persist=True)
    Printer.success("Config was updated.")


def purge():
    """Purge the sandbox config values."""
    SandboxConfigManager.purge()
    Printer.success("Sandbox config was removed.")
