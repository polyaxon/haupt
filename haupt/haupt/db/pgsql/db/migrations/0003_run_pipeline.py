import django.db.models.deletion

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("db", "0002_auto_20200807_1247"),
    ]

    operations = [
        migrations.AddField(
            model_name="run",
            name="pipeline",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="pipeline_runs",
                to="db.Run",
            ),
        ),
    ]
