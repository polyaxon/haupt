#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
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
set_logging(
    context=context,
    root_dir=config.config_root_dir,
    log_level=config.log_level,
    log_handlers=config.log_handlers,
    debug=config.is_debug_mode,
)
set_admin(context=context, config=config)
set_secrets(context=context, config=config)
if config.is_streams_service:
    from haupt.common.settings.services.streams import set_service
elif config.is_scheduler:
    from haupt.common.settings.services.background import set_service
else:
    from haupt.common.settings.services.api import set_service

set_service(context=context, config=config)

from haupt.common.settings.defaults import *

# Service configs
if not config.is_scheduler:
    from .rest import *
