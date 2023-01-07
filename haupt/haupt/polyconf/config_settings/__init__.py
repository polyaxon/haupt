#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

# isort: skip_file

# Default configs

from haupt.common.settings.logging import set_logging
from haupt.common.settings.admin import set_admin
from haupt.common.settings.secrets import set_secrets
from haupt.polyconf.config_manager import config

context = locals()
set_logging(context=context, config=config)
set_admin(context=context, config=config)
set_secrets(context=context, config=config)
if config.is_streams_service:
    from haupt.common.settings.services.streams import set_service
elif config.is_api_service:
    from haupt.common.settings.services.api import set_service
else:
    from haupt.common.settings.services.background import set_service

set_service(context=context, config=config)

from haupt.common.settings.defaults import *

if config.is_api_service or config.is_streams_service:
    from .rest import *
