#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt.common.apis.regex import OWNER_NAME_PATTERN, PROJECT_NAME_PATTERN

# Projects
URLS_PROJECTS_CREATE = r"^{}/projects/create/?$".format(OWNER_NAME_PATTERN)
URLS_PROJECTS_LIST = r"^{}/projects/list/?$".format(OWNER_NAME_PATTERN)
URLS_PROJECTS_NAMES = r"^{}/projects/names/?$".format(OWNER_NAME_PATTERN)
URLS_PROJECTS_DETAILS = r"^{}/{}/?$".format(OWNER_NAME_PATTERN, PROJECT_NAME_PATTERN)

# Resources
URLS_PROJECTS_RUNS_TAG = r"^{}/{}/runs/tag/?$".format(
    OWNER_NAME_PATTERN, PROJECT_NAME_PATTERN
)
URLS_PROJECTS_RUNS_STOP = r"^{}/{}/runs/stop/?$".format(
    OWNER_NAME_PATTERN, PROJECT_NAME_PATTERN
)
URLS_PROJECTS_RUNS_APPROVE = r"^{}/{}/runs/approve/?$".format(
    OWNER_NAME_PATTERN, PROJECT_NAME_PATTERN
)
URLS_PROJECTS_RUNS_DELETE = r"^{}/{}/runs/delete/?$".format(
    OWNER_NAME_PATTERN, PROJECT_NAME_PATTERN
)
URLS_PROJECTS_RUNS_SYNC = r"^{}/{}/runs/sync/?$".format(
    OWNER_NAME_PATTERN, PROJECT_NAME_PATTERN
)
URLS_PROJECTS_RUNS_ARTIFACTS_LINEAGE_V0 = r"^{}/{}/runs/artifacts_lineage/?$".format(
    OWNER_NAME_PATTERN, PROJECT_NAME_PATTERN
)
URLS_PROJECTS_RUNS_ARTIFACTS_LINEAGE = r"^{}/{}/runs/lineage/artifacts/?$".format(
    OWNER_NAME_PATTERN, PROJECT_NAME_PATTERN
)
URLS_PROJECTS_RUNS_LIST = r"^{}/{}/runs/?$".format(
    OWNER_NAME_PATTERN, PROJECT_NAME_PATTERN
)
