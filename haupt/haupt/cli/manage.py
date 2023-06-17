from typing import List, Optional

import click


@click.command()
@click.option(
    "-c",
    "--command",
    help="The command to execute.",
)
@click.argument("args", nargs=-1)
def manage(command: str, args: Optional[List[str]]):
    """Start a new sever session."""
    from haupt.cli.runners.manage import run_manage

    return run_manage(command, args)
