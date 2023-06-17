import os

from typing import List, Optional

from haupt import settings
from haupt.cli.runners.base import manage
from polyaxon.env_vars.keys import EV_KEYS_SERVICE
from polyaxon.services.values import PolyaxonServices


def run_manage(command: str, args: Optional[List[str]] = None):
    os.environ[EV_KEYS_SERVICE] = PolyaxonServices.API
    settings.set_sandbox_config()
    manage(command, args)
