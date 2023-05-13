from django.db import migrations, models


def migrate_wait_time(apps, schema_editor):
    Run = apps.get_model("db", "Run")

    runs = []
    for r in Run.objects.annotate(
        calc_wait_time=models.F("started_at") - models.F("created_at")
    ):
        if r.calc_wait_time:
            r.wait_time = r.calc_wait_time.seconds
            runs.append(r)

    Run.objects.bulk_update(runs, ["wait_time"])


class Migration(migrations.Migration):
    dependencies = [
        ("db", "0007_auto_20201121_1332"),
    ]

    operations = [
        migrations.AddField(
            model_name="run",
            name="wait_time",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.RunPython(migrate_wait_time),
    ]
