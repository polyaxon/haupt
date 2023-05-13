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
                    ("created", "created"),
                    ("resuming", "resuming"),
                    ("on_schedule", "on_schedule"),
                    ("compiled", "compiled"),
                    ("queued", "queued"),
                    ("scheduled", "scheduled"),
                    ("starting", "starting"),
                    ("running", "running"),
                    ("processing", "processing"),
                    ("stopping", "stopping"),
                    ("failed", "failed"),
                    ("stopped", "stopped"),
                    ("succeeded", "succeeded"),
                    ("skipped", "skipped"),
                    ("warning", "warning"),
                    ("unschedulable", "unschedulable"),
                    ("upstream_failed", "upstream_failed"),
                    ("retrying", "retrying"),
                    ("unknown", "unknown"),
                    ("done", "done"),
                ],
                db_index=True,
                default="created",
                max_length=16,
                null=True,
            ),
        ),
    ]
