#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

import re

import django.core.validators

from django.db import migrations, models

import haupt.common.validation.blacklist


class Migration(migrations.Migration):

    dependencies = [
        ("db", "0006_auto_20201020_1705"),
    ]

    operations = [
        migrations.AddField(
            model_name="run",
            name="is_approved",
            field=models.BooleanField(
                default=True,
                help_text="If this entity requires approval before it should run.",
            ),
        ),
        migrations.AlterField(
            model_name="project",
            name="name",
            field=models.CharField(
                max_length=128,
                validators=[
                    django.core.validators.RegexValidator(
                        re.compile("^[-a-zA-Z0-9_]+\\Z"),
                        "Enter a valid “slug” consisting of letters, numbers, underscores or hyphens.",
                        "invalid",
                    ),
                    haupt.common.validation.blacklist.validate_blacklist_name,
                ],
            ),
        ),
        migrations.AlterField(
            model_name="artifact",
            name="name",
            field=models.CharField(db_index=True, max_length=128),
        ),
        migrations.AlterField(
            model_name="run",
            name="name",
            field=models.CharField(
                blank=True,
                default=None,
                max_length=128,
                null=True,
                validators=[
                    django.core.validators.RegexValidator(
                        re.compile("^[-a-zA-Z0-9_]+\\Z"),
                        "Enter a valid “slug” consisting of letters, numbers, underscores or hyphens.",
                        "invalid",
                    ),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="run",
            name="status",
            field=models.CharField(
                blank=True,
                choices=[
                    ("compiled", "compiled"),
                    ("created", "created"),
                    ("done", "done"),
                    ("failed", "failed"),
                    ("on_schedule", "on_schedule"),
                    ("processing", "processing"),
                    ("queued", "queued"),
                    ("resuming", "resuming"),
                    ("retrying", "retrying"),
                    ("running", "running"),
                    ("scheduled", "scheduled"),
                    ("skipped", "skipped"),
                    ("starting", "starting"),
                    ("stopped", "stopped"),
                    ("stopping", "stopping"),
                    ("succeeded", "succeeded"),
                    ("unknown", "unknown"),
                    ("unschedulable", "unschedulable"),
                    ("upstream_failed", "upstream_failed"),
                    ("warning", "warning"),
                ],
                db_index=True,
                default="created",
                max_length=16,
                null=True,
            ),
        ),
    ]
