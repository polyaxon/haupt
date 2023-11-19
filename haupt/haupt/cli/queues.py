from typing import Optional

from clipped.utils.imports import import_string

import click


@click.command()
@click.option(
    "--app",
    default="haupt",
)
@click.option("--service", default="all")
def queues(app: Optional[str], service: Optional[str]):
    app = app or "haupt"
    queues_manager = import_string(f"{app}.background.celeryp.queues.CeleryQueues")
    print(getattr(queues_manager, service)())
