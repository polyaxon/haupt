#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
import time
import uuid

from functools import reduce
from operator import or_
from typing import Any, Dict, List, Set

from django.db import IntegrityError, transaction
from django.db.models import Q

from haupt.db.abstracts.getter import get_artifact_model, get_lineage_model
from haupt.db.abstracts.projects import Owner
from haupt.db.abstracts.runs import BaseRun
from traceml.artifacts import V1RunArtifact


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


def set_run_lineage(run: BaseRun, artifacts_by_keys: Dict, query: Any):
    artifacts_to_link = (
        get_artifact_model().objects.filter(query).only("id", "name", "state")
    )
    lineage_model = get_lineage_model()
    for m in artifacts_to_link:
        lineage_model.objects.get_or_create(
            artifact_id=m.id,
            run_id=run.id,
            is_input=artifacts_by_keys[(m.name, m.state)].is_input,
        )


def update_artifacts(to_update: Set, artifacts_by_keys: Dict):
    updated = []
    for m in to_update:
        artifact = artifacts_by_keys[(m.name, m.state)]
        m.kind = artifact.kind
        m.path = artifact.path
        m.summary = artifact.summary
        updated.append(m)
    get_artifact_model().objects.bulk_update(updated, ["kind", "path", "summary"])


def set_artifacts(run: BaseRun, artifacts: List[V1RunArtifact]):
    if not artifacts:
        return

    artifact_model = get_artifact_model()
    namespace = Owner.uuid

    artifacts_by_keys = get_artifacts_by_keys(
        run=run, namespace=namespace, artifacts=artifacts
    )
    artifacts_keys = list(artifacts_by_keys.keys())
    query = reduce(or_, (Q(name=name, state=state) for name, state in artifacts_keys))
    to_update = artifact_model.objects.filter(query)
    _to_update = {(m.name, m.state) for m in to_update}
    to_create = {m for m in artifacts_keys if m not in _to_update}

    if to_create:
        artifacts_to_create = []
        for m in to_create:
            a = artifacts_by_keys[m]
            artifacts_to_create.append(
                artifact_model(
                    name=a.name,
                    kind=a.kind,
                    path=a.path,
                    state=m[1],
                    summary=a.summary,
                )
            )
        artifact_model.objects.bulk_create(artifacts_to_create)

    update_artifacts(to_update=to_update, artifacts_by_keys=artifacts_by_keys)
    set_run_lineage(run=run, artifacts_by_keys=artifacts_by_keys, query=query)


@transaction.atomic
def atomic_set_artifacts(run: BaseRun, artifacts: List[V1RunArtifact]):
    retries = 0
    while retries < 2:
        try:
            return set_artifacts(run=run, artifacts=artifacts)
        except IntegrityError:
            retries += 1
            time.sleep(0.01)
