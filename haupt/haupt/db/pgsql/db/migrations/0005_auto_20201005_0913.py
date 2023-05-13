import django.core.serializers.json

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("db", "0004_auto_20200905_1523"),
    ]

    operations = [
        migrations.AlterField(
            model_name="artifact",
            name="summary",
            field=models.JSONField(),
        ),
        migrations.AlterField(
            model_name="artifactlineage",
            name="is_input",
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AlterField(
            model_name="run",
            name="inputs",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="run",
            name="meta_info",
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
        migrations.AlterField(
            model_name="run",
            name="outputs",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="run",
            name="params",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="run",
            name="status_conditions",
            field=models.JSONField(
                blank=True,
                default=dict,
                encoder=django.core.serializers.json.DjangoJSONEncoder,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="first_name",
            field=models.CharField(
                blank=True, max_length=150, verbose_name="first name"
            ),
        ),
    ]
