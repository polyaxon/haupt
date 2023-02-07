#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.


from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("db", "0012_alter_artifact_updated_at_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="artifact",
            name="name",
            field=models.CharField(db_index=True, max_length=256),
        ),
    ]
