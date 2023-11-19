import click

from haupt.cli.manage import manage
from haupt.cli.proxies import proxy
from haupt.cli.queues import queues
from haupt.cli.sandbox import sandbox
from haupt.cli.server import server
from haupt.cli.streams import streams
from haupt.cli.viewer import viewer
from polyaxon.logger import clean_outputs, configure_logger


@click.group()
@click.option(
    "-v", "--verbose", is_flag=True, default=False, help="Turn on debug logging"
)
@clean_outputs
def cli(verbose):
    """Haupt -  Lineage metadata API, artifacts streams, sandbox, ML-API, and spaces for Polyaxon.

    Check the help available for each command listed below by appending `-h`.
    """
    configure_logger(verbose)


cli.add_command(proxy)
cli.add_command(manage)
cli.add_command(sandbox)
cli.add_command(server)
cli.add_command(streams)
cli.add_command(viewer)
cli.add_command(queues)
