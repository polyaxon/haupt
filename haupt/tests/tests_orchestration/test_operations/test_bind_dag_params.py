from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import uuid

from django.test import TestCase

from haupt.orchestration.operations.service import OperationsService
from polyaxon._contexts import keys as ctx_keys, paths as ctx_paths
from polyaxon._polyaxonfile import CompiledOperationSpecification, read_polyaxonfile
from polyaxon._utils.fqn_utils import get_project_instance, get_run_instance
from polyaxon.schemas import V1CloningKind, V1Statuses


def make_run():
    created_at = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    return SimpleNamespace(
        uuid=uuid.UUID("0123456789abcdef0123456789abcdef"),
        name="parent-dag",
        status=V1Statuses.RUNNING,
        get_last_condition=lambda: {"type": V1Statuses.RUNNING, "status": True},
        project=SimpleNamespace(
            name="project",
            uuid=uuid.UUID("fedcba9876543210fedcba9876543210"),
            owner=SimpleNamespace(name="owner"),
        ),
        created_at=created_at,
        schedule_at=created_at + timedelta(minutes=1),
        started_at=created_at + timedelta(minutes=2),
        finished_at=created_at + timedelta(minutes=3),
        duration=60,
        cloning_kind=V1CloningKind.COPY,
    )


def bind(params, dag_spec=None):
    op_spec = read_polyaxonfile(
        {"params": params, "run": {"kind": "job", "container": {"image": "test"}}}
    )
    dag_spec = CompiledOperationSpecification.read(
        {"run": {"kind": "dag"}, **(dag_spec or {})}
    )
    OperationsService._bind_dag_params(op_spec, make_run(), dag_spec)
    return op_spec.params


class TestBindDagParams(TestCase):
    def test_binds_every_dag_global(self):
        run = make_run()
        owner, project, run_uuid = "owner", "project", run.uuid.hex
        expected = {
            "uid": run_uuid,
            "id": run_uuid,
            ctx_keys.UUID: run_uuid,
            ctx_keys.NAME: run.name,
            ctx_keys.STATUS: run.status,
            ctx_keys.CONDITION: run.get_last_condition(),
            ctx_keys.OWNER_NAME: owner,
            ctx_keys.PROJECT_UUID: run.project.uuid.hex,
            ctx_keys.PROJECT_NAME: project,
            ctx_keys.PROJECT_UNIQUE_NAME: get_project_instance(owner, project),
            ctx_keys.RUN_INFO: get_run_instance(owner, project, run_uuid),
            ctx_keys.CONTEXT_PATH: ctx_paths.CONTEXT_ROOT,
            ctx_keys.ARTIFACTS_PATH: ctx_paths.CONTEXT_MOUNT_ARTIFACTS,
            ctx_keys.RUN_ARTIFACTS_PATH: (
                ctx_paths.CONTEXT_MOUNT_ARTIFACTS_FORMAT.format(run_uuid)
            ),
            ctx_keys.RUN_OUTPUTS_PATH: (
                ctx_paths.CONTEXT_MOUNT_RUN_OUTPUTS_FORMAT.format(run_uuid)
            ),
            ctx_keys.CREATED_AT: run.created_at,
            ctx_keys.SCHEDULE_AT: run.schedule_at,
            ctx_keys.STARTED_AT: run.started_at,
            ctx_keys.FINISHED_AT: run.finished_at,
            ctx_keys.DURATION: run.duration,
            ctx_keys.CLONING_KIND: run.cloning_kind,
        }
        params = bind(
            {key: {"ref": "dag", "value": "globals.{}".format(key)} for key in expected}
        )

        assert {key: param.value for key, param in params.items()} == expected
        assert all(param.ref is None for param in params.values())

    def test_inputs_and_contexts_take_precedence_over_globals(self):
        params = bind(
            {
                "from_input": {"ref": "dag", "value": "globals.name"},
                "from_context": {"ref": "dag", "value": "globals.status"},
                "plain_input": {
                    "ref": "dag",
                    "value": "inputs.count",
                    "contextOnly": True,
                },
            },
            dag_spec={
                "inputs": [
                    {"name": "name", "type": "str", "value": "input-name"},
                    {"name": "count", "type": "int", "value": 3, "toInit": True},
                ],
                "contexts": [{"name": "status", "type": "str", "value": "ctx"}],
            },
        )

        assert params["from_input"].value == "input-name"
        assert params["from_context"].value == "ctx"
        assert params["plain_input"].value == 3
        assert params["plain_input"].to_init is True
        assert params["plain_input"].context_only is True

    def test_unknown_globals_and_other_refs_are_left_unbound(self):
        params = bind(
            {
                "unknown": {"ref": "dag", "value": "globals.unknown"},
                "upstream": {"ref": "ops.upstream", "value": "outputs.loss"},
                "literal": {"value": 1},
            }
        )

        assert params["unknown"].ref == "dag"
        assert params["unknown"].value == "globals.unknown"
        assert params["upstream"].ref == "ops.upstream"
        assert params["upstream"].value == "outputs.loss"
        assert params["literal"].value == 1
