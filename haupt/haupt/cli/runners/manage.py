import logging
import os

from typing import List, Optional

from clipped.utils.lists import to_list

from haupt import settings
from polyaxon._contexts import paths as ctx_paths
from polyaxon._env_vars.keys import ENV_KEYS_SERVICE, ENV_KEYS_UI_IN_SANDBOX
from polyaxon._services.values import PolyaxonServices

_logger = logging.getLogger("haupt.cli.manage")


def manage(command: str, args: Optional[List[str]] = None):
    from django.core.management import execute_from_command_line

    # Required env var to trigger a management command
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "haupt.polyconf.settings")

    argv = ["manage.py"]
    if command:
        argv.append(command)
    argv += to_list(args, check_none=True)
    execute_from_command_line(argv)


def migrate(
    migrate_tables: bool = False,
    migrate_db: bool = False,
):
    # Required env var to trigger a management command
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "haupt.polyconf.settings")

    if migrate_tables:
        _logger.info("Starting tables migration ...")
        manage("tables")
        _logger.info("Tables were migrated correctly!")

    if migrate_db:
        manage("migrate")
        _logger.info("DB Migration finished!")


def run_manage(command: str, args: Optional[List[str]] = None):
    os.environ[ENV_KEYS_SERVICE] = PolyaxonServices.API
    os.environ[ENV_KEYS_UI_IN_SANDBOX] = "true"
    settings.set_sandbox_config(path=ctx_paths.CONTEXT_ARTIFACTS_ROOT)
    manage(command, args)
