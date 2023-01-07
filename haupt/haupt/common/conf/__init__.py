#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from django.conf import settings

from haupt.common.conf.option_manager import option_manager
from haupt.common.conf.option_service import OptionService
from haupt.common.service_interface import LazyServiceWrapper


def get_conf_backend_path():
    return settings.CONF_BACKEND or "haupt.common.conf.service.ConfService"


def get_conf_options():
    return {"check_ownership": settings.CONF_CHECK_OWNERSHIP}


backend = LazyServiceWrapper(
    backend_base=OptionService,
    backend_path=get_conf_backend_path(),
    options=get_conf_options(),
)
backend.expose(locals())

subscribe = option_manager.subscribe
