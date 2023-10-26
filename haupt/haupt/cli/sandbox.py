import os

import click

from polyaxon.logger import clean_outputs


@click.group()
@clean_outputs
def sandbox():
    """Command for sandbox."""


@sandbox.command()
@click.option(
    "--host",
    help="The service host.",
)
@click.option(
    "--port",
    type=int,
    help="The service port.",
)
@click.option(
    "--workers",
    type=int,
    help="Number of workers.",
)
@click.option(
    "--per-core",
    is_flag=True,
    default=False,
    help="To enable workers per core.",
)
@click.option(
    "--path",
    help="The sandbox root path.",
)
@click.option(
    "--uds",
    help="UNIX domain socket binding.",
)
def start(
    host: str,
    port: int,
    workers: int,
    per_core: bool,
    path: str,
    uds: str,
):
    """Start a new sandbox session."""
    from haupt.cli.runners.sandbox import start
    from polyaxon._cli.config import set_home_path

    path = path or "."
    set_home_path(home_path=path)

    return start(host=host, port=port, workers=workers, per_core=per_core, uds=uds)


@sandbox.command()
@clean_outputs
def show_config():
    """Show the current sandbox config."""
    from haupt.cli.runners.config import show

    return show()


@sandbox.command()
@clean_outputs
@click.option(
    "--host",
    help="The service host.",
)
@click.option(
    "--port",
    type=int,
    help="The service port.",
)
@click.option(
    "--workers",
    type=int,
    help="Number of workers.",
)
@click.option(
    "--per-core",
    is_flag=True,
    default=False,
    help="To enable workers per core.",
)
@click.option(
    "--path",
    help="The sandbox root path.",
)
def set_config(
    host: str,
    port: int,
    workers: int,
    per_core: bool,
    path: str,
):
    """Set the current sandbox config."""
    from haupt.cli.runners.config import set

    return set(
        host=host,
        port=port,
        workers=workers,
        per_core=per_core,
        path=path,
    )


@sandbox.command()
@clean_outputs
def purge_config():
    """Purge the current sandbox config."""
    from haupt.cli.runners.config import purge

    return purge()
