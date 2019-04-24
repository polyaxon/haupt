# Generated by Django 2.2 on 2019-04-23 20:41

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('db', '0021_auto_20190418_1600_std_backend_is_managed'),
    ]

    operations = [
        migrations.RenameField(
            model_name='operation',
            old_name='celery_queue',
            new_name='queue',
        ),
        migrations.RenameField(
            model_name='operationrun',
            old_name='celery_task_context',
            new_name='context',
        ),
        migrations.RemoveField(
            model_name='operation',
            name='celery_task',
        ),
        migrations.RemoveField(
            model_name='operation',
            name='config',
        ),
        migrations.RemoveField(
            model_name='operation',
            name='run_as_user',
        ),
        migrations.RemoveField(
            model_name='operationrun',
            name='celery_task_id',
        ),
        migrations.RemoveField(
            model_name='operationrun',
            name='finished_at',
        ),
        migrations.RemoveField(
            model_name='operationrun',
            name='started_at',
        ),
        migrations.RemoveField(
            model_name='operationrun',
            name='status',
        ),
        migrations.AddField(
            model_name='operation',
            name='content',
            field=models.TextField(blank=True, help_text='The yaml content of the polyaxonfile/specification.', null=True),
        ),
        migrations.AddField(
            model_name='operation',
            name='entity_type',
            field=models.CharField(blank=True, max_length=24, null=True),
        ),
        migrations.AddField(
            model_name='operation',
            name='security_context',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, help_text='security context to impersonate while running the operation.', max_length=64, null=True),
        ),
        migrations.AddField(
            model_name='operationrun',
            name='entity_content_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='operationrun',
            name='entity_object_id',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='operationrun',
            name='status',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.DeleteModel(
            name='OperationRunStatus',
        ),
    ]
