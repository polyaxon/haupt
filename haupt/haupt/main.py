#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

import click

from haupt.cli.sandbox import sandbox
from haupt.cli.streams import streams
from polyaxon import settings
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
@click.pass_context
@clean_outputs
def cli(context, verbose, offline):
    """Haupt -  Lineage metadata API, artifacts streams, sandbox, ML-API, and spaces for Polyaxon.

    Check the help available for each command listed below by appending `-h`.
    """
    settings.set_cli_config()
    configure_logger(verbose)


cli.add_command(sandbox)
cli.add_command(streams)


def main():
    cli(auto_envvar_prefix="HAUPT_CLI")
