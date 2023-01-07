#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt.db.abstracts.projects import BaseProject


class Project(BaseProject):
    class Meta(BaseProject.Meta):
        app_label = "db"
        db_table = "db_project"
