#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from marshmallow import ValidationError

from polyaxon.services.values import PolyaxonServices
from polyaxon.utils.formatting import Printer

PROXIES_CONFIG = None
SANDBOX_CONFIG = None

PolyaxonServices.set_service_name()


def set_proxies_config():
    from haupt.managers.proxies import ProxiesManager

    global PROXIES_CONFIG

    PROXIES_CONFIG = ProxiesManager.get_config_from_env()


def set_sandbox_config():
    from haupt.managers.sandbox import SandboxConfigManager
    from polyaxon.contexts.paths import mount_sandbox
    from polyaxon.settings import set_agent_config

    mount_sandbox()
    PolyaxonServices.set_service_name(PolyaxonServices.SANDBOX)

    global SANDBOX_CONFIG

    try:
        SANDBOX_CONFIG = SandboxConfigManager.get_config_or_default()
        set_agent_config(SANDBOX_CONFIG)
    except (TypeError, ValidationError):
        SandboxConfigManager.purge()
        Printer.print_warning("Your sandbox configuration was purged!")
