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
    from polyaxon._cli.config import set_home_path

    if path:
        set_home_path(home_path=path)

    return run_manage(command, args)
