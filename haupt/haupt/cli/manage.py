from typing import List, Optional

import click


@click.command(
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    )
)
@click.option(
    "--app",
    default="haupt",
)
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
def manage(app: Optional[str], command: str, path: str, args: Optional[List[str]]):
    """Start a new sever session."""
    if app and app != "haupt":
        from haupt.cli.runners.manage import manage

        return manage(command, args, app=app)

    from haupt.cli.runners.manage import run_manage
    from polyaxon._cli.config import set_home_path

    if path:
        set_home_path(home_path=path)

    return run_manage(command, args)
