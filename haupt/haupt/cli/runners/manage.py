import os

from typing import List, Optional

from haupt import settings
from haupt.cli.runners.base import manage
from polyaxon.env_vars.keys import EV_KEYS_SERVICE, EV_KEYS_UI_IN_SANDBOX
from polyaxon.services.values import PolyaxonServices


def run_manage(command: str, args: Optional[List[str]] = None):
    os.environ[EV_KEYS_SERVICE] = PolyaxonServices.API
    os.environ[EV_KEYS_UI_IN_SANDBOX] = "true"
    settings.set_sandbox_config()
    manage(command, args)
