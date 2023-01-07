#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt.db.abstracts.artifacts import BaseArtifact, BaseArtifactLineage


class Artifact(BaseArtifact):
    class Meta:
        app_label = "db"
        unique_together = (("name", "state"),)
        db_table = "db_artifact"


class ArtifactLineage(BaseArtifactLineage):
    class Meta:
        app_label = "db"
        unique_together = (("run", "artifact", "is_input"),)
        db_table = "db_artifactlineage"
