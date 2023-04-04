#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from typing import Dict, List, Optional

from haupt.db.abstracts.getter import get_run_model
from haupt.db.abstracts.runs import BaseRun
from polyaxon.lifecycle import V1StatusCondition, V1Statuses
from polyaxon.polyflow import V1CompiledOperation, V1RunKind
from polyaxon.schemas import V1RunPending


def create_run(
    project_id: int,
    user_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    readme: Optional[str] = None,
    tags: List[int] = None,
    raw_content: Optional[str] = None,
    meta_info: Optional[Dict] = None,
) -> BaseRun:
    instance = get_run_model().objects.create(
        project_id=project_id,
        user_id=user_id,
        name=name,
        description=description,
        readme=readme,
        tags=tags,
        kind=V1RunKind.JOB,
        is_managed=False,
        raw_content=raw_content,
        meta_info=meta_info,
        status_conditions=[
            V1StatusCondition.get_condition(
                type=V1Statuses.CREATED,
                status="True",
                reason="ModelManager",
                message="Run is created",
            ).to_dict()
        ],
    )
    return instance


def base_approve_run(run: BaseRun):
    pending = run.pending
    if pending:
        new_pending = None
        if (
            (pending == V1RunPending.BUILD and run.status == V1Statuses.CREATED)
            or pending == V1RunPending.UPLOAD
        ) and run.content:
            compiled_operation = V1CompiledOperation.read(
                run.content
            )  # TODO: Use construct
            if compiled_operation.is_approved is False:
                new_pending = V1RunPending.APPROVAL
        run.pending = new_pending
        run.save(update_fields=["pending", "updated_at"])
