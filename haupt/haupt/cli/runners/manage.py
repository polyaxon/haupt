import logging
import os

from typing import List, Optional

from clipped.utils.lists import to_list

_logger = logging.getLogger("haupt.cli.manage")


def manage(
    command: Optional[str], args: Optional[List[str]] = None, app: Optional[str] = None
):
    from django.core.management import execute_from_command_line

    app = app or "haupt"

    # Required env var to trigger a management command
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"{app}.polyconf.settings")

    argv = ["manage.py"]
    if command:
        argv.append(command)
    argv += to_list(args, check_none=True)
    execute_from_command_line(argv)


def migrate(
    migrate_tables: bool = False,
    migrate_db: bool = False,
):
    if migrate_tables:
        _logger.info("Starting tables migration ...")
        manage("tables")
        _logger.info("Tables were migrated correctly!")

    if migrate_db:
        manage("migrate")
        _logger.info("DB Migration finished!")


def run_manage(command: str, args: Optional[List[str]] = None):
    from haupt import settings
    from polyaxon._env_vars.keys import ENV_KEYS_SERVICE, ENV_KEYS_UI_IN_SANDBOX
    from polyaxon._services.values import PolyaxonServices

    if command == "runserver":
        os.environ[ENV_KEYS_SERVICE] = PolyaxonServices.API
    if os.environ.get(ENV_KEYS_SERVICE, PolyaxonServices.API) == PolyaxonServices.API:
        os.environ[ENV_KEYS_UI_IN_SANDBOX] = "true"
        settings.set_sandbox_config()
    manage(command, args)
