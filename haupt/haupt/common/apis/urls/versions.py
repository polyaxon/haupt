#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
from haupt.common.apis.regex import INSTALLATION_PATTERN, NAME_PATTERN, VERSION_PATTERN

URLS_VERSIONS_INSTALLED = r"^installation/?$"
URLS_VERSIONS_LOG_HANDLER = r"^log_handler/?$"
URLS_VERSIONS_COMPATIBILITY = r"^compatibility/{}/{}/{}/?$".format(
    INSTALLATION_PATTERN, VERSION_PATTERN, NAME_PATTERN
)
