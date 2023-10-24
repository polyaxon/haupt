import os

from typing import List, Optional

import click


@click.command()
@click.option(
    "-c",
    "--command",
    help="The command to execute.",
)
@click.option(
    "--path",
    help="The sandbox root path.",
)
@click.argument("args", nargs=-1)
def manage(command: str, path: str, args: Optional[List[str]]):
    """Start a new sever session."""
    from haupt.cli.runners.manage import run_manage
    from polyaxon._env_vars.keys import ENV_KEYS_SANDBOX_ROOT

    if path:
        os.environ[ENV_KEYS_SANDBOX_ROOT] = path

    return run_manage(command, args)
