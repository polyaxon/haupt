from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("db", "0003_run_pipeline"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="project",
            name="deleted",
        ),
        migrations.RemoveField(
            model_name="run",
            name="deleted",
        ),
        migrations.AddField(
            model_name="project",
            name="live_state",
            field=models.IntegerField(
                blank=True,
                choices=[
                    (1, "live"),
                    (0, "archived"),
                    (-1, "deletion_progressing"),
                ],
                default=1,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="run",
            name="live_state",
            field=models.IntegerField(
                blank=True,
                choices=[
                    (1, "live"),
                    (0, "archived"),
                    (-1, "deletion_progressing"),
                ],
                default=1,
                null=True,
            ),
        ),
    ]
