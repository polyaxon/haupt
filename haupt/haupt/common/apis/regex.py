#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

UUID_KEY = "uuid"
OWNER_KEY = "uuid"
NAME_KEY = "name"
USERNAME_KEY = "username"
VERSION_KEY = "version"
VERSION_PATTERN = r"(?P<version>[-\w]{1,16})"
INSTALLATION_KEY = "installation"
INSTALLATION_PATTERN = r"(?P<installation>\w{1,36})"
UUID_PATTERN = r"(?P<uuid>\w{1,36})"
SLUG_PATTERN = r"[-\w]{1,256}"
USERNAME_PATTERN = r"(?P<username>[-\w]{1,128})"
OWNER_NAME_KEY = "owner_name"
PROJECT_OWNER_NAME_KEY = "project_owner_name"
OWNER_NAME_PATTERN = r"(?P<owner_name>[-\w]{1,128})"
PROJECT_NAME_KEY = "project_name"
PROJECT_NAME_PATTERN = r"(?P<project_name>[-\w]{1,128})"
ARTIFACT_NAME_PATTERN = r"(?P<artifact_name>[-\w]{1,128})"
ARTIFACT_NAME_KEY = "artifact_name"
NAME_PATTERN = r"(?P<name>[-\w]{1,256})"
SEQUENCE_PATTERN = r"(?P<sequence>\d+)"
ID_PATTERN = r"(?P<id>\d+)"
INDEX_PATTERN = r"(?P<index>\d+)"
RUN_ID_PATTERN = r"(?P<run_id>\d+)"
RUN_UUID_KEY = "run_uuid"
RUN_UUID_PATTERN = r"(?P<run_uuid>\w{1,36})"

EVENT_KIND_PATTERN = r"(?P<event_kind>[-\w]{1,20})"
EVENT_NAME_PATTERN = r"(?P<event_name>[-\w]{1,128})"

ANY_CONSUMER_PATTERN = r"?(?P<path>.*)/?"
