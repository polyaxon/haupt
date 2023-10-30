import json

from typing import List

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder

from haupt.common.db.inserter import RawBulkInserter
from haupt.db.abstracts.runs import BaseRun
from haupt.db.defs import Models

_RUN_FIELDS = (
    "description",
    "created_at",
    "updated_at",
    "live_state",
    "tags",
    "uuid",
    "started_at",
    "finished_at",
    "wait_time",
    "duration",
    "status",
    "status_conditions",
    "state",
    "readme",
    "component_state",
    "raw_content",
    "content",
    "name",
    "kind",
    "runtime",
    "project_id",
    "managed_by",
    "pending",
    "meta_info",
    "params",
    "inputs",
    "outputs",
    "original_id",
    "pipeline_id",
    "cloning_kind",
    "controller_id",
    "schedule_at",
    "user_id",
)

if settings.HAS_ORG_MANAGEMENT:
    _RUN_FIELDS += (
        "namespace",
        "artifacts_store_id",
        "agent_id",
        "queue_id",
    )


def _process_field(run: BaseRun, field: str):
    value = getattr(run, field)
    if field in {"status_conditions", "meta_info", "inputs", "outputs", "params"}:
        return json.dumps(value, cls=DjangoJSONEncoder)
    return value


def bulk_create_runs(runs: List[BaseRun], fetch_ids: bool = False):
    if settings.DB_ENGINE_NAME == "sqlite":
        Models.Run.objects.bulk_create(runs)
        return
    inserter = RawBulkInserter(Models.Run, _RUN_FIELDS, fetch_ids=fetch_ids)
    for run in runs:
        inserter.queue_row(*[_process_field(run, i) for i in _RUN_FIELDS])

    inserter.insert()
