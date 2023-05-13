from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("db", "0009_project_unique_name"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="run",
            name="is_approved",
        ),
        migrations.AddField(
            model_name="run",
            name="pending",
            field=models.CharField(
                blank=True,
                choices=[
                    ("approval", "approval"),
                    ("upload", "upload"),
                    ("cache", "cache"),
                    ("build", "build"),
                ],
                db_index=True,
                help_text="If this entity requires approval before it should run.",
                max_length=8,
                null=True,
            ),
        ),
    ]
