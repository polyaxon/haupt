#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

# Setting values to None means using defaults

from haupt import pkg
from polyaxon import dist

ENCRYPTION_BACKEND = None
CONF_CHECK_OWNERSHIP = False
AUDITOR_BACKEND = None
AUDITOR_EVENTS_TASK = None
WORKERS_BACKEND = None
EXECUTOR_BACKEND = "haupt.orchestration.executor.service.ExecutorService"
WORKERS_SERVICE = "haupt.common.workers"
EXECUTOR_SERVICE = "haupt.orchestration.executor"
OPERATIONS_BACKEND = None
PLATFORM_VERSION = pkg.VERSION
PLATFORM_DIST = dist.CE
CONF_BACKEND = "haupt.common.conf.service.ConfService"
STORE_OPTION = "env"
K8S_IN_CLUSTER = True
