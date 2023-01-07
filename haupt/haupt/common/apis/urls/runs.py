#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt.common.apis.regex import (
    ARTIFACT_NAME_PATTERN,
    OWNER_NAME_PATTERN,
    PROJECT_NAME_PATTERN,
    RUN_UUID_PATTERN,
)

URLS_RUNS_CREATE = r"^{}/{}/runs/create/?$".format(
    OWNER_NAME_PATTERN, PROJECT_NAME_PATTERN
)
URLS_RUNS_LIST = r"^{}/runs/list/?$".format(OWNER_NAME_PATTERN, PROJECT_NAME_PATTERN)
URLS_RUNS_DETAILS = r"^{}/{}/runs/{}/?$".format(
    OWNER_NAME_PATTERN, PROJECT_NAME_PATTERN, RUN_UUID_PATTERN
)
URLS_RUNS_RESTART = r"^{}/{}/runs/{}/restart/?$".format(
    OWNER_NAME_PATTERN, PROJECT_NAME_PATTERN, RUN_UUID_PATTERN
)
URLS_RUNS_RESUME = r"^{}/{}/runs/{}/resume/?$".format(
    OWNER_NAME_PATTERN, PROJECT_NAME_PATTERN, RUN_UUID_PATTERN
)
URLS_RUNS_COPY = r"^{}/{}/runs/{}/copy/?$".format(
    OWNER_NAME_PATTERN, PROJECT_NAME_PATTERN, RUN_UUID_PATTERN
)
URLS_RUNS_STOP = r"^{}/{}/runs/{}/stop/?$".format(
    OWNER_NAME_PATTERN, PROJECT_NAME_PATTERN, RUN_UUID_PATTERN
)
URLS_RUNS_APPROVE = r"^{}/{}/runs/{}/approve/?$".format(
    OWNER_NAME_PATTERN, PROJECT_NAME_PATTERN, RUN_UUID_PATTERN
)
URLS_RUNS_STATUSES = r"^{}/{}/runs/{}/statuses/?$".format(
    OWNER_NAME_PATTERN, PROJECT_NAME_PATTERN, RUN_UUID_PATTERN
)
URLS_RUNS_NAMESPACE = r"^{}/{}/runs/{}/namespace/?$".format(
    OWNER_NAME_PATTERN, PROJECT_NAME_PATTERN, RUN_UUID_PATTERN
)
URLS_RUNS_ARTIFACTS_LINEAGE_LIST_V0 = r"^{}/{}/runs/{}/artifacts_lineage/?$".format(
    OWNER_NAME_PATTERN, PROJECT_NAME_PATTERN, RUN_UUID_PATTERN
)
URLS_RUNS_ARTIFACTS_LINEAGE_NAMES_V0 = (
    r"^{}/{}/runs/{}/artifacts_lineage/names/?$".format(
        OWNER_NAME_PATTERN, PROJECT_NAME_PATTERN, RUN_UUID_PATTERN
    )
)
URLS_RUNS_ARTIFACTS_LINEAGE_DETAILS_V0 = (
    r"^{}/{}/runs/{}/artifacts_lineage/{}/?$".format(
        OWNER_NAME_PATTERN,
        PROJECT_NAME_PATTERN,
        RUN_UUID_PATTERN,
        ARTIFACT_NAME_PATTERN,
    )
)
URLS_RUNS_ARTIFACTS_LINEAGE_LIST = r"^{}/{}/runs/{}/lineage/artifacts/?$".format(
    OWNER_NAME_PATTERN, PROJECT_NAME_PATTERN, RUN_UUID_PATTERN
)
URLS_RUNS_ARTIFACTS_LINEAGE_NAMES = r"^{}/{}/runs/{}/lineage/artifacts/names/?$".format(
    OWNER_NAME_PATTERN, PROJECT_NAME_PATTERN, RUN_UUID_PATTERN
)
URLS_RUNS_ARTIFACTS_LINEAGE_DETAILS = r"^{}/{}/runs/{}/lineage/artifacts/{}/?$".format(
    OWNER_NAME_PATTERN, PROJECT_NAME_PATTERN, RUN_UUID_PATTERN, ARTIFACT_NAME_PATTERN
)
