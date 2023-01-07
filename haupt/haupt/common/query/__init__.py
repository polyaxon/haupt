#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt.common.query.service import QueryService
from haupt.common.service_interface import LazyServiceWrapper

backend = LazyServiceWrapper(
    backend_base=QueryService,
    backend_path="haupt.common.query.service.QueryService",
    options={},
)
backend.expose(locals())
