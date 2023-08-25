# Generated by Django 4.2.4 on 2023-08-25 11:40

import django.db.models.deletion

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("db", "0013_major_upgrade"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="run",
            name="is_managed",
        ),
        migrations.AddField(
            model_name="project",
            name="archived_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="project",
            name="deleted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="run",
            name="archived_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="run",
            name="deleted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="ProjectStats",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("user_count", models.IntegerField(blank=True, default=0, null=True)),
                ("run_count", models.IntegerField(blank=True, default=0, null=True)),
                ("model_count", models.IntegerField(blank=True, default=0, null=True)),
                (
                    "artifact_count",
                    models.IntegerField(blank=True, default=0, null=True),
                ),
                (
                    "component_count",
                    models.IntegerField(blank=True, default=0, null=True),
                ),
                (
                    "tracking_time",
                    models.IntegerField(blank=True, default=0, null=True),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="stats",
                        to="db.project",
                    ),
                ),
            ],
            options={
                "db_table": "db_projectstats",
                "abstract": False,
            },
        ),
    ]