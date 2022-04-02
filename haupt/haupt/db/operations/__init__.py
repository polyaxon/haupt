#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from django.conf import settings

from common.service_interface import LazyServiceWrapper
from db.operations.service import OperationInitSpec, OperationsService


def get_operation_backend_path():
    return settings.OPERATIONS_BACKEND or "db.operations.service.OperationsService"


backend = LazyServiceWrapper(
    backend_base=OperationsService,
    backend_path=get_operation_backend_path(),
    options={},
)
backend.expose(locals())
