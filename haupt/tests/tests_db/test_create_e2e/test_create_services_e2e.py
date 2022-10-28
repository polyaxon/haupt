#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from django.test import TestCase

from haupt.common.test_cases.fixtures import (
    get_fxt_service,
    get_fxt_service_with_inputs,
)
from haupt.db.factories.projects import ProjectFactory
from haupt.db.factories.users import UserFactory
from haupt.db.models.runs import Run
from haupt.orchestration import operations
from polyaxon.polyaxonfile import CompiledOperationSpecification, OperationSpecification
from polyaxon.polyflow import V1RunKind


class TestCreateServices(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.project = ProjectFactory()

    def test_create_run_with_service_spec(self):
        count = Run.objects.count()
        config_dict = get_fxt_service()
        spec = OperationSpecification.read(values=config_dict)
        run = operations.init_and_save_run(
            project_id=self.project.id, user_id=self.user.id, op_spec=spec
        )
        assert Run.objects.count() == count + 1
        assert run.kind == V1RunKind.SERVICE
        assert run.name == "foo"
        assert run.description == "a description"
        assert set(run.tags) == {"backend", "lab", "tag1", "tag2"}
        service_spec = CompiledOperationSpecification.read(run.content)
        assert service_spec.run.container.image == "jupyter"

    def test_create_run_with_templated_service_spec(self):
        count = Run.objects.count()
        config_dict = get_fxt_service_with_inputs()
        spec = OperationSpecification.read(values=config_dict)
        run = operations.init_and_save_run(
            project_id=self.project.id, user_id=self.user.id, op_spec=spec
        )
        assert Run.objects.count() == count + 1
        assert run.kind == V1RunKind.SERVICE
        assert run.name == "foo"
        assert run.description == "a description"
        assert set(run.tags) == {"backend", "lab"}
        job_spec = CompiledOperationSpecification.read(run.content)
        assert job_spec.run.container.image == "{{ image }}"
        compiled_operation = CompiledOperationSpecification.read(run.content)
        compiled_operation = CompiledOperationSpecification.apply_params(
            compiled_operation, params=spec.params
        )
        compiled_operation = CompiledOperationSpecification.apply_operation_contexts(
            compiled_operation
        )
        CompiledOperationSpecification.apply_runtime_contexts(compiled_operation)
        run.content = compiled_operation.to_dict(dump=True)
        run.save(update_fields=["content"])
        job_spec = CompiledOperationSpecification.read(run.content)
        job_spec = CompiledOperationSpecification.apply_runtime_contexts(job_spec)
        assert job_spec.run.container.image == "foo/bar"
