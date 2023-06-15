from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("db", "0013_major_upgrade"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="run",
            name="is_managed",
        ),
    ]
