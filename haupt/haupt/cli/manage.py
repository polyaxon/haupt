import click


@click.command()
@click.option(
    "-c",
    "--command",
    help="The command to execute.",
)
def manage(command: str):
    """Start a new sever session."""
    from haupt.cli.runners.manage import run_manage

    return run_manage(command)
