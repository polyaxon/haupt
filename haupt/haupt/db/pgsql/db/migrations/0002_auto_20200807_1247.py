#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("db", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="run",
            old_name="run_time",
            new_name="duration",
        ),
    ]
