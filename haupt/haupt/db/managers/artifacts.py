from functools import reduce
from operator import or_
import time
from typing import Any, Dict, Iterable, List
import uuid

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Q

from haupt.db.abstracts.projects import Owner
from haupt.db.abstracts.runs import BaseRun
from haupt.db.defs import Models
from traceml.artifacts import V1ArtifactKind, V1RunArtifact


def get_artifacts_by_keys(
    run: BaseRun, namespace: uuid.UUID, artifacts: List[V1RunArtifact]
) -> Dict:
    results = {}
    for m in artifacts:
        state = m.state
        if not state:
            if m.is_input:
                state = m.get_state(namespace)
            else:
                state = run.uuid
        elif not isinstance(state, uuid.UUID):
            try:
                state = uuid.UUID(state)
            except (ValueError, KeyError):
                state = uuid.uuid5(namespace, state)
        results[(m.name, state)] = m

    return results


def get_artifacts_query(owner: Any, keys: Iterable) -> Q:
    query = reduce(or_, (Q(name=name, state=state) for name, state in keys))
    if settings.HAS_ORG_MANAGEMENT:
        query = Q(owner=owner) & query
    return query


def set_run_lineage(run: BaseRun, artifacts_by_keys: Dict, artifacts: List):
    # `is_input=None` is stored as an output link (`False`): NULLs never conflict in
    # the unique constraint.
    linked = set(
        Models.ArtifactLineage.objects.filter(
            run_id=run.id, artifact_id__in=[m.id for m in artifacts]
        ).values_list("artifact_id", "is_input")
    )
    to_link = []
    for m in artifacts:
        is_input = bool(artifacts_by_keys[(m.name, m.state)].is_input)
        if (m.id, is_input) not in linked:
            to_link.append(
                Models.ArtifactLineage(
                    artifact_id=m.id, run_id=run.id, is_input=is_input
                )
            )
    if to_link:
        Models.ArtifactLineage.objects.bulk_create(to_link, ignore_conflicts=True)


def update_artifacts(to_update: List, artifacts_by_keys: Dict):
    updated = []
    for m in to_update:
        artifact = artifacts_by_keys[(m.name, m.state)]
        m.kind = artifact.kind
        m.path = artifact.path
        m.summary = artifact.summary
        updated.append(m)
    Models.Artifact.objects.bulk_update(updated, ["kind", "path", "summary"])


def set_artifacts(run: BaseRun, artifacts: List[V1RunArtifact]):
    if not artifacts:
        return

    owner = run.project.owner
    namespace = owner.uuid if settings.HAS_ORG_MANAGEMENT else Owner.uuid

    artifacts_by_keys = get_artifacts_by_keys(
        run=run, namespace=namespace, artifacts=artifacts
    )
    existing = list(
        Models.Artifact.objects.filter(get_artifacts_query(owner, artifacts_by_keys))
    )
    existing_keys = {(m.name, m.state) for m in existing}
    to_create = [m for m in artifacts_by_keys if m not in existing_keys]

    has_iteration_kind = False
    has_metrics = False
    owner_filter = {"owner": owner} if settings.HAS_ORG_MANAGEMENT else {}
    if to_create:
        artifacts_to_create = []
        for m in to_create:
            a = artifacts_by_keys[m]
            if a.kind == V1ArtifactKind.METRIC and not a.is_input:
                has_metrics = True
            if a.kind == V1ArtifactKind.ITERATION and not a.is_input:
                has_iteration_kind = True
            artifacts_to_create.append(
                Models.Artifact(
                    **owner_filter,
                    name=a.name,
                    kind=a.kind,
                    path=a.path,
                    state=m[1],
                    summary=a.summary,
                )
            )
        Models.Artifact.objects.bulk_create(artifacts_to_create)

    update_artifacts(to_update=existing, artifacts_by_keys=artifacts_by_keys)
    # `bulk_create` doesn't return ids on every backend, so fetch only the new rows.
    created = []
    if to_create:
        created = list(
            Models.Artifact.objects.filter(get_artifacts_query(owner, to_create)).only(
                "id", "name", "state"
            )
        )
    set_run_lineage(
        run=run, artifacts_by_keys=artifacts_by_keys, artifacts=existing + created
    )
    # Handle iteration lineage
    # if has_iteration_kind:
    #     workers.send(SchedulerCeleryTasks.RUNS_ITERATE, kwargs={"run_id": run.id})
    # TODO: Add intermediate metric early


def atomic_set_artifacts(run: BaseRun, artifacts: List[V1RunArtifact]):
    # One savepoint per attempt: on PostgreSQL a failed statement aborts the
    # whole transaction, so a retry in the same block can never succeed.
    for _ in range(2):
        try:
            with transaction.atomic():
                return set_artifacts(run=run, artifacts=artifacts)
        except IntegrityError:
            time.sleep(0.01)
