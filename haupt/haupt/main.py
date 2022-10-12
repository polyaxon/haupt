#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

import click

from haupt.cli.sandbox import sandbox
from haupt.cli.streams import streams
from polyaxon.logger import clean_outputs, configure_logger


@click.group()
@click.option(
    "-v", "--verbose", is_flag=True, default=False, help="Turn on debug logging"
)
@click.option(
    "--offline",
    is_flag=True,
    default=False,
    help="Run command in offline mode if supported. "
    "Currently used for run command in --local mode.",
)
@clean_outputs
def cli(verbose):
    """Haupt -  Lineage metadata API, artifacts streams, sandbox, ML-API, and spaces for Polyaxon.

    Check the help available for each command listed below by appending `-h`.
    """
    configure_logger(verbose)


cli.add_command(sandbox)
cli.add_command(streams)


def main():
    cli(auto_envvar_prefix="HAUPT_CLI")
