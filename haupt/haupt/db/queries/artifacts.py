#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
from typing import Dict, List

from django.conf import settings

from haupt.db.abstracts.getter import get_lineage_model

lineage_model = get_lineage_model()

artifacts_names = lineage_model.objects.prefetch_related("artifact").only(
    "artifact__id", "artifact__name"
)

artifacts = (
    lineage_model.objects.prefetch_related("artifact")
    .only(
        "is_input",
        "artifact__id",
        "artifact__name",
        "artifact__kind",
        "artifact__path",
        "artifact__state",
        "artifact__summary",
    )
    .distinct()
)

project_runs_artifacts = (
    lineage_model.objects.prefetch_related("artifact", "run")
    .only(
        "is_input",
        "artifact__id",
        "artifact__name",
        "artifact__kind",
        "artifact__path",
        "artifact__state",
        "artifact__summary",
        "run__id",
        "run__uuid",
        "run__name",
    )
    .distinct()
)

project_runs_artifacts_distinct = lineage_model.objects.prefetch_related(
    "artifact"
).only(
    "is_input",
    "artifact__name",
    "artifact__kind",
)
if settings.DB_ENGINE_NAME == "sqlite":
    project_runs_artifacts_distinct = project_runs_artifacts_distinct.distinct()
else:
    project_runs_artifacts_distinct = project_runs_artifacts_distinct.distinct(
        "is_input",
        "artifact__name",
        "artifact__kind",
    )


def clean_sqlite_distinct_artifacts(data: List[Dict]):
    """Sqlite does not provide a distinct logic based on columns"""
    distinct_data = []
    data_ids = set([])
    count = 0
    for d in data:
        d_id = "{}-{}-{}".format(d["is_input"], d["name"], d["kind"])
        if d_id not in data_ids:
            data_ids.add(d_id)
            distinct_data.append(d)
            count += 1

    return distinct_data, count
