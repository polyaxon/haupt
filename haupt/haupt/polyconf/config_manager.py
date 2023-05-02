#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt.managers.platform import PlatformManager
from polyaxon.settings import HOME_CONFIG

PlatformManager.set_config_path(HOME_CONFIG.path)
PLATFORM_CONFIG = PlatformManager.get_config_from_env(file_path=__file__)
