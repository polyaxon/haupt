import re
import uuid

import django.contrib.auth.models
import django.contrib.auth.validators
import django.core.serializers.json
import django.core.validators
import django.db.models.deletion
import django.utils.timezone

from django.conf import settings
from django.db import migrations, models

import haupt.common.validation.blacklist

from polyaxon import schemas


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
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
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "username",
                    models.CharField(
                        error_messages={
                            "unique": "A user with that username already exists."
                        },
                        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
                        max_length=150,
                        unique=True,
                        validators=[
                            django.contrib.auth.validators.UnicodeUsernameValidator()
                        ],
                        verbose_name="username",
                    ),
                ),
                (
                    "first_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="first name"
                    ),
                ),
                (
                    "last_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="last name"
                    ),
                ),
                (
                    "email",
                    models.EmailField(
                        blank=True, max_length=254, verbose_name="email address"
                    ),
                ),
                (
                    "is_staff",
                    models.BooleanField(
                        default=False,
                        help_text="Designates whether the user can log into this admin site.",
                        verbose_name="staff status",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.",
                        verbose_name="active",
                    ),
                ),
                (
                    "date_joined",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="date joined"
                    ),
                ),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "user",
                "verbose_name_plural": "users",
                "db_table": "db_user",
                "abstract": False,
                "swappable": "AUTH_USER_MODEL",
            },
            managers=[
                ("objects", django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name="Artifact",
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
                ("state", models.UUIDField(db_index=True)),
                ("name", models.CharField(db_index=True, max_length=256)),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("model", "model"),
                            ("audio", "audio"),
                            ("video", "video"),
                            ("histogram", "histogram"),
                            ("image", "image"),
                            ("tensor", "tensor"),
                            ("dataframe", "dataframe"),
                            ("chart", "chart"),
                            ("csv", "csv"),
                            ("tsv", "tsv"),
                            ("psv", "psv"),
                            ("ssv", "ssv"),
                            ("metric", "metric"),
                            ("env", "env"),
                            ("html", "html"),
                            ("text", "text"),
                            ("file", "file"),
                            ("dir", "dir"),
                            ("dockerfile", "dockerfile"),
                            ("docker_image", "docker_image"),
                            ("data", "data"),
                            ("coderef", "coderef"),
                            ("table", "table"),
                            ("tensorboard", "tensorboard"),
                            ("curve", "curve"),
                            ("confusion", "confusion"),
                            ("analysis", "analysis"),
                            ("iteration", "iteration"),
                            ("markdown", "markdown"),
                            ("system", "system"),
                            ("artifact", "artifact"),
                            ("span", "span"),
                        ],
                        db_index=True,
                        max_length=12,
                    ),
                ),
                ("path", models.CharField(blank=True, max_length=256, null=True)),
                ("summary", models.JSONField()),
            ],
            options={
                "db_table": "db_artifact",
                "unique_together": {("name", "state")},
            },
        ),
        migrations.CreateModel(
            name="ArtifactLineage",
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
                ("is_input", models.BooleanField(blank=True, default=False, null=True)),
                (
                    "artifact",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="runs_lineage",
                        to="db.artifact",
                    ),
                ),
            ],
            options={
                "db_table": "db_artifactlineage",
            },
        ),
        migrations.CreateModel(
            name="Project",
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
                ("description", models.TextField(blank=True, null=True)),
                (
                    "live_state",
                    models.IntegerField(
                        blank=True,
                        choices=[
                            (1, "live"),
                            (0, "archived"),
                            (-1, "deletion_progressing"),
                        ],
                        db_index=True,
                        default=schemas.LiveState["LIVE"],
                        null=True,
                    ),
                ),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("archived_at", models.DateTimeField(blank=True, null=True)),
                (
                    "tags",
                    models.JSONField(
                        blank=True,
                        encoder=django.core.serializers.json.DjangoJSONEncoder,
                        null=True,
                    ),
                ),
                (
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("readme", models.TextField(blank=True, null=True)),
                (
                    "name",
                    models.CharField(
                        max_length=128,
                        unique=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                re.compile("^[-a-zA-Z0-9_]+\\Z"),
                                "Enter a valid “slug” consisting of letters, numbers, underscores or hyphens.",
                                "invalid",
                            ),
                            haupt.common.validation.blacklist.validate_blacklist_name,
                        ],
                    ),
                ),
                (
                    "contributors",
                    models.ManyToManyField(
                        blank=True, related_name="+", to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
            options={
                "db_table": "db_project",
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Run",
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
                    "live_state",
                    models.IntegerField(
                        blank=True,
                        choices=[
                            (1, "live"),
                            (0, "archived"),
                            (-1, "deletion_progressing"),
                        ],
                        db_index=True,
                        default=schemas.LiveState["LIVE"],
                        null=True,
                    ),
                ),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("archived_at", models.DateTimeField(blank=True, null=True)),
                (
                    "tags",
                    models.JSONField(
                        blank=True,
                        encoder=django.core.serializers.json.DjangoJSONEncoder,
                        null=True,
                    ),
                ),
                (
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("readme", models.TextField(blank=True, null=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("wait_time", models.FloatField(blank=True, null=True)),
                ("duration", models.FloatField(blank=True, null=True)),
                (
                    "schedule_at",
                    models.DateTimeField(blank=True, db_index=True, null=True),
                ),
                (
                    "checked_at",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        default=django.utils.timezone.now,
                        null=True,
                    ),
                ),
                ("memory", models.FloatField(blank=True, default=0, null=True)),
                ("cpu", models.FloatField(blank=True, default=0, null=True)),
                ("gpu", models.FloatField(blank=True, default=0, null=True)),
                ("custom", models.FloatField(blank=True, default=0, null=True)),
                ("cost", models.FloatField(blank=True, default=0, null=True)),
                (
                    "raw_content",
                    models.TextField(
                        blank=True,
                        help_text="The raw yaml content of the polyaxonfile/specification.",
                        null=True,
                    ),
                ),
                (
                    "content",
                    models.TextField(
                        blank=True,
                        help_text="The compiled yaml content of the polyaxonfile/specification.",
                        null=True,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        blank=True,
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
                        db_index=True,
                        default=schemas.V1Statuses["CREATED"],
                        max_length=16,
                        null=True,
                    ),
                ),
                (
                    "status_conditions",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        encoder=django.core.serializers.json.DjangoJSONEncoder,
                        null=True,
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        blank=True,
                        default=None,
                        max_length=128,
                        null=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                re.compile("^[-a-zA-Z0-9_]+\\Z"),
                                "Enter a valid “slug” consisting of letters, numbers, underscores or hyphens.",
                                "invalid",
                            )
                        ],
                    ),
                ),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("job", "job"),
                            ("service", "service"),
                            ("dag", "dag"),
                            ("daskjob", "daskjob"),
                            ("rayjob", "rayjob"),
                            ("mpijob", "mpijob"),
                            ("tfjob", "tfjob"),
                            ("pytorchjob", "pytorchjob"),
                            ("paddlejob", "paddlejob"),
                            ("mxjob", "mxjob"),
                            ("xgbjob", "xgbjob"),
                            ("matrix", "matrix"),
                            ("schedule", "schedule"),
                            ("tuner", "tuner"),
                            ("watchdog", "watchdog"),
                            ("notifier", "notifier"),
                            ("cleaner", "cleaner"),
                            ("builder", "builder"),
                        ],
                        db_index=True,
                        max_length=12,
                    ),
                ),
                (
                    "runtime",
                    models.CharField(
                        blank=True, db_index=True, max_length=12, null=True
                    ),
                ),
                (
                    "managed_by",
                    models.CharField(
                        blank=True,
                        choices=[("user", "user"), ("cli", "cli"), ("agent", "agent")],
                        db_index=True,
                        default=schemas.ManagedBy["AGENT"],
                        max_length=5,
                        null=True,
                    ),
                ),
                (
                    "pending",
                    models.CharField(
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
                ("meta_info", models.JSONField(blank=True, default=dict, null=True)),
                ("params", models.JSONField(blank=True, null=True)),
                ("inputs", models.JSONField(blank=True, null=True)),
                ("outputs", models.JSONField(blank=True, null=True)),
                (
                    "component_state",
                    models.UUIDField(blank=True, db_index=True, null=True),
                ),
                (
                    "cloning_kind",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("copy", "copy"),
                            ("restart", "restart"),
                            ("cache", "cache"),
                        ],
                        max_length=12,
                        null=True,
                    ),
                ),
                (
                    "artifacts",
                    models.ManyToManyField(
                        blank=True,
                        related_name="runs",
                        through="db.ArtifactLineage",
                        to="db.artifact",
                    ),
                ),
                (
                    "contributors",
                    models.ManyToManyField(
                        blank=True, related_name="+", to=settings.AUTH_USER_MODEL
                    ),
                ),
                (
                    "controller",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="controller_runs",
                        to="db.run",
                    ),
                ),
                (
                    "original",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="clones",
                        to="db.run",
                    ),
                ),
                (
                    "pipeline",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="pipeline_runs",
                        to="db.run",
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="runs",
                        to="db.project",
                    ),
                ),
            ],
            options={
                "db_table": "db_run",
                "abstract": False,
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
                    models.JSONField(
                        blank=True,
                        encoder=django.core.serializers.json.DjangoJSONEncoder,
                        null=True,
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
        migrations.AddField(
            model_name="run",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="+",
                to=settings.AUTH_USER_MODEL,
            ),
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
                    models.JSONField(
                        blank=True,
                        encoder=django.core.serializers.json.DjangoJSONEncoder,
                        null=True,
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
                    "contributors",
                    models.ManyToManyField(
                        blank=True, related_name="+", to=settings.AUTH_USER_MODEL
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
            },
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
                ("updated_at", models.DateTimeField(auto_now=True, db_index=True)),
                ("created_at", models.DateTimeField(db_index=True)),
                (
                    "user",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        encoder=django.core.serializers.json.DjangoJSONEncoder,
                        null=True,
                    ),
                ),
                (
                    "run",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        encoder=django.core.serializers.json.DjangoJSONEncoder,
                        null=True,
                    ),
                ),
                (
                    "status",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        encoder=django.core.serializers.json.DjangoJSONEncoder,
                        null=True,
                    ),
                ),
                (
                    "version",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        encoder=django.core.serializers.json.DjangoJSONEncoder,
                        null=True,
                    ),
                ),
                (
                    "tracking_time",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        encoder=django.core.serializers.json.DjangoJSONEncoder,
                        null=True,
                    ),
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
        migrations.AddField(
            model_name="project",
            name="latest_stats",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="db.projectstats",
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
        migrations.AddField(
            model_name="artifactlineage",
            name="run",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="artifacts_lineage",
                to="db.run",
            ),
        ),
        migrations.AddIndex(
            model_name="run",
            index=models.Index(fields=["name"], name="db_run_name_47fc7c_idx"),
        ),
        migrations.AddIndex(
            model_name="projectversion",
            index=models.Index(fields=["name"], name="db_projectv_name_3ea950_idx"),
        ),
        migrations.AlterUniqueTogether(
            name="projectversion",
            unique_together={("project", "name", "kind")},
        ),
        migrations.AddIndex(
            model_name="project",
            index=models.Index(fields=["name"], name="db_project_name_4bfc0e_idx"),
        ),
        migrations.AlterUniqueTogether(
            name="artifactlineage",
            unique_together={("run", "artifact", "is_input")},
        ),
    ]
