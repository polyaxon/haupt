import os

import click


@click.command()
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
    help="The service host.",
)
@click.option(
    "--uds",
    help="UNIX domain socket binding.",
)
def sandbox(
    host: str,
    port: int,
    workers: int,
    per_core: bool,
    path: str,
    uds: str,
):
    """Start a new sandbox session."""
    from haupt.cli.runners.sandbox import start
    from polyaxon.env_vars.keys import EV_KEYS_SANDBOX_ROOT

    if path:
        os.environ[EV_KEYS_SANDBOX_ROOT] = path

    return start(host=host, port=port, workers=workers, per_core=per_core, uds=uds)
