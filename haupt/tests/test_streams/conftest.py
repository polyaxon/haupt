#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.


import os
import tempfile


def pytest_configure():
    os.environ["POLYAXON_NO_CONFIG"] = "true"
    os.environ["POLYAXON_CONTEXT_ROOT"] = tempfile.mkdtemp()
    os.environ["POLYAXON_OFFLINE_ROOT"] = tempfile.mkdtemp()
    os.environ["POLYAXON_ARTIFACTS_ROOT"] = tempfile.mkdtemp()
