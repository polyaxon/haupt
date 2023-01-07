#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt.common import conf
from haupt.common.options.registry import installation

conf.subscribe(installation.PlatformEnvironmentVersion)
conf.subscribe(installation.PlatformVersion)
conf.subscribe(installation.PlatformDist)
conf.subscribe(installation.PlatformHost)
conf.subscribe(installation.ChartVersion)
conf.subscribe(installation.OrganizationKey)
