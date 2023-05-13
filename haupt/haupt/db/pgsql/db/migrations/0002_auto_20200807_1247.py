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
