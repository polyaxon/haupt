#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

import os

from haupt.schemas.proxies_config import ProxiesConfig
from polyaxon.config.manager import ConfigManager
from polyaxon.managers.base import BaseConfigManager, ManagerVisibility


class ProxiesManager(BaseConfigManager):
    """Manages proxies configuration file."""

    VISIBILITY = ManagerVisibility.GLOBAL
    CONFIG_FILE_NAME = ".proxies"
    CONFIG = ProxiesConfig

    @classmethod
    def get_config_from_env(cls, **kwargs) -> ProxiesConfig:
        config_paths = [os.environ, {"dummy": "dummy"}]

        proxy_config = ConfigManager.read_configs(config_paths)
        return ProxiesConfig.from_dict(proxy_config.data)
