#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

# Setting values to None means using defaults

import pkg

from polyaxon import dist

ENCRYPTION_BACKEND = None
CONF_CHECK_OWNERSHIP = False
AUDITOR_BACKEND = None
AUDITOR_EVENTS_TASK = None
WORKERS_BACKEND = None
EXECUTOR_BACKEND = "db.executor.service.ExecutorService"
WORKERS_SERVICE = "common.workers"
EXECUTOR_SERVICE = "db.executor"
OPERATIONS_BACKEND = None
PLATFORM_VERSION = pkg.VERSION
PLATFORM_DIST = dist.CE
CONF_BACKEND = "common.conf.service.ConfService"
STORE_OPTION = "env"
K8S_IN_CLUSTER = True
