import re
import uuid

import django.contrib.postgres.fields
import django.utils.timezone

from django.db import migrations, models

from polyaxon import schemas


def migrate_is_managed_by(apps, schema_editor):
    Run = apps.get_model("db", "Run")
    Run.objects.filter(is_managed=True).update(managed_by=schemas.ManagedBy.AGENT.value)
    Run.objects.filter(is_managed=False).update(managed_by=schemas.ManagedBy.USER.value)


class Migration(migrations.Migration):
    dependencies = [
        ("db", "0012_alter_artifact_updated_at_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="run",
            name="managed_by",
            field=models.CharField(
                blank=True,
                choices=[("user", "user"), ("cli", "cli"), ("agent", "agent")],
                db_index=True,
                max_length=5,
                default=schemas.ManagedBy["AGENT"],
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="run",
            name="is_managed",
            field=models.BooleanField(
                default=True,
                help_text="If this entity is managed by the platform (deprecated).",
            ),
        ),
        migrations.AddField(
            model_name="run",
            name="component_state",
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="run",
            name="checked_at",
            field=models.DateTimeField(
                blank=True, db_index=True, default=django.utils.timezone.now, null=True
            ),
        ),
        migrations.AddField(
            model_name="run",
            name="controller",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="controller_runs",
                to="db.run",
            ),
        ),
        migrations.AddField(
            model_name="run",
            name="cost",
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name="run",
            name="cpu",
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name="run",
            name="custom",
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name="run",
            name="gpu",
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name="run",
            name="memory",
            field=models.FloatField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name="run",
            name="schedule_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="run",
            name="state",
            field=models.UUIDField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name="artifact",
            name="name",
            field=models.CharField(db_index=True, max_length=256),
        ),
        migrations.CreateModel(
            name="ProjectVersion",
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
                ("state", models.UUIDField(blank=True, db_index=True, null=True)),
                ("description", models.TextField(blank=True, null=True)),
                (
                    "tags",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=64),
                        blank=True,
                        null=True,
                        size=None,
                    ),
                ),
                (
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("readme", models.TextField(blank=True, null=True)),
                (
                    "stage",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("testing", "testing"),
                            ("staging", "staging"),
                            ("production", "production"),
                            ("disabled", "disabled"),
                        ],
                        db_index=True,
                        default=schemas.V1Stages["TESTING"],
                        max_length=16,
                        null=True,
                    ),
                ),
                (
                    "stage_conditions",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        encoder=django.core.serializers.json.DjangoJSONEncoder,
                        null=True,
                    ),
                ),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("component", "component"),
                            ("model", "model"),
                            ("artifact", "artifact"),
                        ],
                        db_index=True,
                        max_length=12,
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        max_length=128,
                        validators=[
                            django.core.validators.RegexValidator(
                                re.compile("^[-a-zA-Z0-9_.]+\\Z"),
                                "Enter a valid “value” consisting of letters, numbers, underscores, hyphens, or dots.",
                                "invalid",
                            )
                        ],
                    ),
                ),
                (
                    "content",
                    models.TextField(
                        blank=True,
                        help_text="The yaml/json content/metadata.",
                        null=True,
                    ),
                ),
                (
                    "lineage",
                    models.ManyToManyField(
                        blank=True, related_name="versions", to="db.artifactlineage"
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="versions",
                        to="db.project",
                    ),
                ),
                (
                    "run",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="versions",
                        to="db.run",
                    ),
                ),
            ],
            options={
                "db_table": "db_projectversion",
                "abstract": False,
                "indexes": [
                    models.Index(fields=["name"], name="db_projectv_name_3ea950_idx")
                ],
                "unique_together": {("project", "name", "kind")},
            },
        ),
        migrations.CreateModel(
            name="RunEdge",
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
                ("values", models.JSONField(blank=True, null=True)),
                (
                    "kind",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("action", "action"),
                            ("event", "event"),
                            ("hook", "hook"),
                            ("dag", "dag"),
                            ("join", "join"),
                            ("run", "run"),
                            ("tb", "tb"),
                            ("build", "build"),
                            ("manual", "manual"),
                        ],
                        db_index=True,
                        max_length=6,
                        null=True,
                    ),
                ),
                (
                    "statuses",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(
                            choices=[
                                ("created", "created"),
                                ("resuming", "resuming"),
                                ("on_schedule", "on_schedule"),
                                ("compiled", "compiled"),
                                ("queued", "queued"),
                                ("scheduled", "scheduled"),
                                ("starting", "starting"),
                                ("running", "running"),
                                ("processing", "processing"),
                                ("stopping", "stopping"),
                                ("failed", "failed"),
                                ("stopped", "stopped"),
                                ("succeeded", "succeeded"),
                                ("skipped", "skipped"),
                                ("warning", "warning"),
                                ("unschedulable", "unschedulable"),
                                ("upstream_failed", "upstream_failed"),
                                ("retrying", "retrying"),
                                ("unknown", "unknown"),
                                ("done", "done"),
                            ],
                            max_length=16,
                        ),
                        blank=True,
                        null=True,
                        size=None,
                    ),
                ),
                (
                    "downstream",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="upstream_edges",
                        to="db.run",
                    ),
                ),
                (
                    "upstream",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="downstream_edges",
                        to="db.run",
                    ),
                ),
            ],
            options={
                "db_table": "db_runedge",
            },
        ),
        migrations.AddField(
            model_name="run",
            name="upstream_runs",
            field=models.ManyToManyField(
                blank=True,
                related_name="downstream_runs",
                through="db.RunEdge",
                to="db.run",
            ),
        ),
        migrations.CreateModel(
            name="Bookmark",
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
                ("enabled", models.BooleanField(default=True)),
                ("object_id", models.PositiveIntegerField()),
                (
                    "content_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="contenttypes.contenttype",
                    ),
                ),
            ],
            options={
                "verbose_name": "bookmark",
                "verbose_name_plural": "bookmarks",
                "db_table": "db_bookmark",
                "abstract": False,
            },
        ),
        migrations.RunPython(migrate_is_managed_by),
    ]
