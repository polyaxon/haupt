from unittest.mock import patch

from django.test import TestCase

from haupt.db.factories.projects import ProjectFactory
from haupt.db.factories.users import UserFactory
from haupt.db.managers.versions import get_component_version_state
from haupt.db.models.runs import Run
from haupt.orchestration import operations
from polyaxon._flow.run.dag import V1Dag
from polyaxon._polyaxonfile import (
    CompiledOperationSpecification,
    OperationSpecification,
)
from polyaxon._polyaxonfile.specs import read_polyaxonfile
from polyaxon._utils.fixtures import get_fxt_service, get_fxt_service_with_inputs
from polyaxon.schemas import V1Component, V1RunKind


class TestCreateServices(TestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.project = ProjectFactory()

    def test_component_state_preserves_optional_version(self):
        component = V1Component.read(
            {"run": {"kind": V1RunKind.JOB, "container": {"image": "test"}}}
        )

        versionless_state = get_component_version_state(component)
        assert component.version is None
        assert str(versionless_state) == "4de9f1f8-06b5-54dd-b723-3737aeee69d2"

        component.version = 0.4
        versioned_state = get_component_version_state(component)
        assert component.version == 0.4
        assert str(versioned_state) == "18bbe3c5-bfc4-5721-94f9-cf16e712c676"
        assert versioned_state != versionless_state

    def test_shared_component_state_preserves_authored_kind(self):
        for kind in (None, "component", "operation"):
            with self.subTest(kind=kind):
                source = {"run": {"kind": "job", "container": {"image": "test"}}}
                if kind:
                    source["kind"] = kind
                spec = read_polyaxonfile(source)

                state = get_component_version_state(spec)

                assert str(state) == "4de9f1f8-06b5-54dd-b723-3737aeee69d2"
                assert spec.kind == kind
                assert spec.to_dict() == source

    def test_dag_component_state_distinguishes_explicit_nulls(self):
        for explicit_null in (False, True):
            with self.subTest(explicit_null=explicit_null):
                node = {
                    "kind": "operation",
                    "name": "train",
                    "component": {
                        "kind": "component",
                        "run": {
                            "kind": "job",
                            "container": {"image": "busybox:1.36"},
                        },
                    },
                }
                if explicit_null:
                    node.update({"schedule": None, "matrix": None})
                source = {
                    "kind": "component",
                    "run": {"kind": "dag", "operations": [node]},
                }
                component = read_polyaxonfile(source)

                state = get_component_version_state(component)

                if explicit_null:
                    assert str(state) == "a7ae3b97-2926-5e14-991b-3b9747c8759a"
                else:
                    assert str(state) == "88eb9eca-d36f-5763-8d24-5a645a86b700"
                with patch.dict(
                    V1Dag._DUMP_POLICY,
                    {"default": {"exclude_none": True}},
                ):
                    assert get_component_version_state(component) == state
                assert component.to_dict() == source

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
        run.content = compiled_operation.to_json()
        run.save(update_fields=["content"])
        job_spec = CompiledOperationSpecification.read(run.content)
        job_spec = CompiledOperationSpecification.apply_runtime_contexts(job_spec)
        assert job_spec.run.container.image == "foo/bar"
