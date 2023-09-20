from typing import Dict, List, Optional, Tuple

from django.db.models import QuerySet

from haupt.db.abstracts.runs import BaseRun
from haupt.db.defs import Models
from polyaxon.schemas import dags


def get_run_upstream(
    run: BaseRun, id_field: str = "id", pipeline_id: Optional[int] = None
) -> QuerySet:
    upstream_runs = run.upstream_runs
    if pipeline_id:
        upstream_runs = upstream_runs.filter(pipeline_id=pipeline_id)
    return upstream_runs.values_list(id_field, flat=True)


def get_run_downstream(
    run: BaseRun, id_field: str = "id", pipeline_id: Optional[int] = None
) -> QuerySet:
    downstream_runs = run.downstream_runs
    if pipeline_id:
        downstream_runs = downstream_runs.filter(pipeline_id=pipeline_id)
    return downstream_runs.values_list(id_field, flat=True)


def get_run_dag(run: BaseRun) -> Tuple[Dict, Dict]:
    runs = run.pipeline_runs.only("id", "pipeline_id", "uuid").prefetch_related(
        "upstream_runs"
    )
    ops = ((run, get_run_upstream(run)) for run in runs)
    return dags.process_dag(ops)


def get_run_graph(filters) -> Dict[str, List[str]]:
    runs = (
        Models.Run.objects.filter(**filters)
        .only("id", "pipeline_id", "uuid")
        .prefetch_related("downstream_runs")
    )
    return {
        run.uuid.hex: {
            "downstream": [uid.hex for uid in get_run_downstream(run, "uuid")]
        }
        for run in runs
    }
