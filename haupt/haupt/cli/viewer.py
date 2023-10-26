import os

from collections.abc import Mapping
from typing import Dict, Optional

import click


def sanitize_server_config(server_config: Optional[Dict] = None) -> Dict:
    from clipped.formatting import Printer

    if not server_config:
        return {}

    def parse_server_config():
        if isinstance(parse_server_config, Mapping):
            return parse_server_config

        parsed_server_config = {}
        for sc in server_config:
            index = sc.find("=")
            if index == -1:
                message = (
                    "Invalid format for -SC/--server-config option: '%s'. Use -SC name=value."
                    % sc
                )
                Printer.error(message, sys_exit=True)
            name = sc[:index]
            value = sc[index + 1 :]
            if name in parsed_server_config:
                message = "Repeated parameter: '%s'" % name
                Printer.error(message, sys_exit=True)
            parsed_server_config[name] = value

        return parsed_server_config

    server_config = parse_server_config()
    keys = {
        "host",
        "port",
        "workers",
        "per_core",
        "per-core",
        "path",
        "uds",
    }
    return {
        key: server_config[key] for key in keys if server_config.get(key) is not None
    }


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
    help="The sandbox root path.",
)
@click.option(
    "--uds",
    help="UNIX domain socket binding.",
)
def viewer(
    host: str,
    port: int,
    workers: int,
    per_core: bool,
    path: str,
    uds: str,
):
    """Start a new local viewer session."""
    from haupt.cli.runners.viewer import start

    return start(
        host=host, port=port, workers=workers, per_core=per_core, uds=uds, path=path
    )
