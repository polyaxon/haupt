from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("db", "0010_auto_20210429_1539"),
    ]

    operations = [
        migrations.AlterField(
            model_name="artifact",
            name="state",
            field=models.UUIDField(db_index=True),
        ),
    ]
