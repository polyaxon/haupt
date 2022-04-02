#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from common.conf.handlers.env_handler import EnvConfHandler
from common.conf.handlers.settings_handler import SettingsConfHandler
from common.conf.option_service import OptionService
from common.options.option import OptionStores


class ConfService(OptionService):
    def setup(self) -> None:
        super().setup()
        self.stores[OptionStores.SETTINGS] = SettingsConfHandler()
        self.stores[OptionStores.ENV] = EnvConfHandler()
