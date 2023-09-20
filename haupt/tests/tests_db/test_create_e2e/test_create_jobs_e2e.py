from django.test import TestCase

from haupt.db.factories.projects import ProjectFactory
from haupt.db.factories.users import UserFactory
from haupt.db.models.runs import Run
from haupt.orchestration import operations
from polyaxon._polyaxonfile import (
    CompiledOperationSpecification,
    OperationSpecification,
)
from polyaxon._utils.fixtures import get_fxt_job, get_fxt_job_with_inputs
from polyaxon.schemas import V1RunKind


class TestCreateJobs(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.project = ProjectFactory()

    def test_create_run_with_job_spec(self):
        count = Run.objects.count()
        config_dict = get_fxt_job()
        spec = OperationSpecification.read(values=config_dict)
        run = operations.init_and_save_run(
            project_id=self.project.id, user_id=self.user.id, op_spec=spec
        )
        assert Run.objects.count() == count + 1
        assert run.pending is None
        assert run.kind == V1RunKind.JOB
        assert run.name == "foo"
        assert run.description == "a description"
        assert set(run.tags) == {"tag1", "tag2"}
        # Check compiled operation passes
        compiled_operation = CompiledOperationSpecification.read(run.content)
        compiled_operation = CompiledOperationSpecification.apply_params(
            compiled_operation
        )
        CompiledOperationSpecification.apply_runtime_contexts(compiled_operation)
        # Check job
        job_spec = CompiledOperationSpecification.read(run.content)
        assert job_spec.run.container.image == "test"
        job_spec = CompiledOperationSpecification.apply_operation_contexts(job_spec)
        assert job_spec.run.container.image == "test"

    def test_create_run_with_templated_job_spec(self):
        count = Run.objects.count()
        config_dict = get_fxt_job_with_inputs()
        spec = OperationSpecification.read(values=config_dict)
        run = operations.init_and_save_run(
            project_id=self.project.id, user_id=self.user.id, op_spec=spec
        )
        assert Run.objects.count() == count + 1
        assert run.pending is None
        assert run.kind == V1RunKind.JOB
        assert run.name == "foo"
        assert run.description == "a description"
        assert set(run.tags) == {"tag1", "tag2"}  # From template
        compiled_operation = CompiledOperationSpecification.read(run.content)
        compiled_operation = CompiledOperationSpecification.apply_params(
            compiled_operation, params=spec.params
        )
        compiled_operation = CompiledOperationSpecification.apply_operation_contexts(
            compiled_operation
        )
        CompiledOperationSpecification.apply_runtime_contexts(compiled_operation)
        run.content = compiled_operation.to_json()
        run.save(update_fields=["content"])
        job_spec = CompiledOperationSpecification.read(run.content)
        assert job_spec.run.container.image == "{{ image }}"
        job_spec = CompiledOperationSpecification.apply_runtime_contexts(job_spec)
        assert job_spec.run.container.image == "foo/bar"
