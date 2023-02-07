#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("db", "0010_auto_20210429_1539"),
    ]

    operations = [
        migrations.AlterField(
            model_name="artifact",
            name="state",
            field=models.UUIDField(db_index=True),
        ),
    ]
