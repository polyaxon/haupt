import re

import django.core.validators

from django.db import migrations, models

import haupt.common.validation.blacklist


class Migration(migrations.Migration):
    dependencies = [
        ("db", "0008_run_wait_time"),
    ]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="name",
            field=models.CharField(
                max_length=128,
                unique=True,
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
    ]
