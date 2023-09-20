import pytest

from unittest.mock import patch

from rest_framework import status

from haupt.apis.serializers.runs import (
    RunDetailSerializer,
    RunSerializer,
    RunStatusSerializer,
)
from haupt.background.celeryp.tasks import SchedulerCeleryTasks
from haupt.db.factories.projects import ProjectFactory
from haupt.db.factories.runs import RunFactory
from haupt.db.managers.statuses import new_run_status, new_run_stop_status
from haupt.db.models.runs import Run
from haupt.orchestration import operations
from polyaxon._constants.metadata import META_RECOMPILE
from polyaxon._polyaxonfile import OperationSpecification
from polyaxon.api import API_V1
from polyaxon.schemas import (
    LiveState,
    ManagedBy,
    V1RunKind,
    V1RunPending,
    V1StatusCondition,
    V1Statuses,
)
from tests.base.case import (
    BaseTest,
    BaseTestBookmarkCreateView,
    BaseTestBookmarkDeleteView,
)


class BaseTestRunApi(BaseTest):
    model_class = Run
    factory_class = RunFactory

    def setUp(self):
        super().setUp()
        self.project = ProjectFactory()
        self.object = self.factory_class(
            user=self.user,
            project=self.project,
            content="test",
            raw_content="test",
            managed_by=ManagedBy.AGENT,
        )
        self.url = "/{}/{}/{}/runs/{}/".format(
            API_V1, self.user.username, self.project.name, self.object.uuid.hex
        )
        self.queryset = self.model_class.objects.all()


@pytest.mark.run_mark
class TestRunDetailViewV1(BaseTestRunApi):
    serializer_class = RunDetailSerializer

    def test_get(self):
        resp = self.client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK
        self.object.refresh_from_db()
        expected = self.serializer_class(self.object).data
        assert resp.data == expected

    def test_patch_exp(self):
        new_description = "updated_xp_name"
        data = {"description": new_description}
        assert self.object.description != data["description"]
        resp = self.client.patch(self.url, data=data)
        assert resp.status_code == status.HTTP_200_OK
        new_object = self.model_class.objects.get(id=self.object.id)
        assert new_object.user == self.object.user
        assert new_object.description != self.object.description
        assert new_object.description == new_description

        # is_managed
        data = {"is_managed": False}
        assert self.object.is_managed is True
        resp = self.client.patch(self.url, data=data)
        assert resp.status_code == status.HTTP_200_OK
        new_object = self.model_class.objects.get(id=self.object.id)
        assert new_object.is_managed is False
        assert new_object.managed_by == ManagedBy.USER

        # is_managed
        data = {"is_managed": None}
        assert new_object.is_managed is False
        resp = self.client.patch(self.url, data=data)
        # Should raise because the run has no content
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        new_object = self.model_class.objects.get(id=self.object.id)
        assert new_object.is_managed is False
        assert new_object.managed_by == ManagedBy.USER

        # path is_managed
        data = {"is_managed": False}
        assert new_object.is_managed is False
        resp = self.client.patch(self.url, data=data)
        assert resp.status_code == status.HTTP_200_OK
        new_object = self.model_class.objects.get(id=self.object.id)
        assert new_object.is_managed is False
        assert new_object.managed_by == ManagedBy.USER

        # managed_by
        data = {"managed_by": ManagedBy.USER}
        assert self.object.is_managed is True
        resp = self.client.patch(self.url, data=data)
        assert resp.status_code == status.HTTP_200_OK
        new_object = self.model_class.objects.get(id=self.object.id)
        assert new_object.is_managed is False
        assert new_object.managed_by == ManagedBy.USER

        # is_managed
        data = {"managed_by": None}
        assert new_object.is_managed is False
        resp = self.client.patch(self.url, data=data)
        # Should raise because the run has no content
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        new_object = self.model_class.objects.get(id=self.object.id)
        assert new_object.is_managed is False
        assert new_object.managed_by == ManagedBy.USER

        # path is_managed
        data = {"managed_by": ManagedBy.USER}
        assert new_object.is_managed is False
        resp = self.client.patch(self.url, data=data)
        assert resp.status_code == status.HTTP_200_OK
        new_object = self.model_class.objects.get(id=self.object.id)
        assert new_object.is_managed is False
        assert new_object.managed_by == ManagedBy.USER

        # pending
        data = {"pending": V1RunPending.APPROVAL}
        assert self.object.pending is None
        resp = self.client.patch(self.url, data=data)
        assert resp.status_code == status.HTTP_200_OK
        new_object = self.model_class.objects.get(id=self.object.id)
        assert new_object.pending == V1RunPending.APPROVAL

        # pending
        data = {"pending": None}
        assert new_object.pending == V1RunPending.APPROVAL
        resp = self.client.patch(self.url, data=data)
        assert resp.status_code == status.HTTP_200_OK
        new_object = self.model_class.objects.get(id=self.object.id)
        assert new_object.pending is None

        # Update tags
        assert new_object.tags is None
        data = {"tags": ["foo", "bar"]}
        resp = self.client.patch(self.url, data=data)
        assert resp.status_code == status.HTTP_200_OK
        new_object = self.model_class.objects.get(id=self.object.id)
        assert sorted(new_object.tags) == sorted(["foo", "bar"])

        data = {"tags": ["foo_new", "bar_new"], "merge": False}
        resp = self.client.patch(self.url, data=data)
        assert resp.status_code == status.HTTP_200_OK
        new_object = self.model_class.objects.get(id=self.object.id)
        assert sorted(new_object.tags) == sorted(["foo_new", "bar_new"])

        data = {"tags": ["foo", "bar"], "merge": True}
        resp = self.client.patch(self.url, data=data)
        assert resp.status_code == status.HTTP_200_OK
        new_object = self.model_class.objects.get(id=self.object.id)
        assert sorted(new_object.tags) == sorted(["foo_new", "bar_new", "foo", "bar"])

        # Update name
        data = {"name": "new_name"}
        assert new_object.name is None
        resp = self.client.patch(self.url, data=data)
        assert resp.status_code == status.HTTP_200_OK
        new_object = self.model_class.objects.get(id=self.object.id)
        assert new_object.name == data["name"]

    def test_patch_exp_io(self):
        # Update inputs
        assert self.object.inputs is None
        data = {"inputs": {"foo": "bar"}}
        resp = self.client.patch(self.url, data=data)
        assert resp.status_code == status.HTTP_200_OK
        new_object = self.model_class.objects.get(id=self.object.id)
        assert new_object.inputs == {"foo": "bar"}

        data = {"inputs": {"foo_new": "bar_new"}, "merge": False}
        resp = self.client.patch(self.url, data=data)
        assert resp.status_code == status.HTTP_200_OK
        new_object = self.model_class.objects.get(id=self.object.id)
        assert new_object.inputs == {"foo_new": "bar_new"}

        data = {"inputs": {"foo": "bar"}, "merge": True}
        resp = self.client.patch(self.url, data=data)
        assert resp.status_code == status.HTTP_200_OK
        new_object = self.model_class.objects.get(id=self.object.id)
        assert new_object.inputs == {"foo_new": "bar_new", "foo": "bar"}

        # Update outputs
        assert new_object.outputs is None
        data = {"outputs": {"foo": "bar", "loss": 0.001}}
        resp = self.client.patch(self.url, data=data)
        assert resp.status_code == status.HTTP_200_OK
        new_object = self.model_class.objects.get(id=self.object.id)
        assert new_object.outputs == {"foo": "bar", "loss": 0.001}

        data = {"outputs": {"foo_new": "bar_new"}, "merge": False}
        resp = self.client.patch(self.url, data=data)
        assert resp.status_code == status.HTTP_200_OK
        new_object = self.model_class.objects.get(id=self.object.id)
        assert new_object.outputs == {"foo_new": "bar_new"}

        data = {"outputs": {"foo": "bar", "loss": 0.001}, "merge": True}
        resp = self.client.patch(self.url, data=data)
        assert resp.status_code == status.HTTP_200_OK
        new_object = self.model_class.objects.get(id=self.object.id)
        assert new_object.outputs == {"foo_new": "bar_new", "foo": "bar", "loss": 0.001}

    def test_delete_from_created_schedule_archives_and_schedules_stop(self):
        assert self.model_class.objects.count() == 1
        with patch("haupt.common.workers.send") as workers_send:
            resp = self.client.delete(self.url)
        assert workers_send.call_count == 0
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        # Deleted
        assert self.model_class.objects.count() == 0
        assert self.model_class.all.count() == 1  # Async

    def test_delete_from_running_status_archives_and_schedules_stop(self):
        new_run_status(
            self.object,
            condition=V1StatusCondition.get_condition(
                type=V1Statuses.RUNNING, status=True
            ),
        )
        assert self.model_class.objects.count() == 1
        with patch("haupt.common.workers.send") as workers_send:
            resp = self.client.delete(self.url)
        assert workers_send.call_count == 0
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        # Deleted
        assert self.model_class.objects.count() == 0
        assert self.model_class.all.count() == 1
        assert self.model_class.all.last().live_state == LiveState.DELETION_PROGRESSING


@pytest.mark.run_mark
class TestRunArchiveRestoreViewV1(BaseTestRunApi):
    def test_archive_schedule_deletion(self):
        new_run_status(
            self.object,
            condition=V1StatusCondition.get_condition(
                type=V1Statuses.RUNNING, status=True
            ),
        )
        assert self.model_class.objects.count() == 1
        with patch("haupt.common.workers.send") as workers_send:
            resp = self.client.post(self.url + "archive/")
        assert workers_send.call_count == 0
        assert resp.status_code == status.HTTP_200_OK
        assert self.model_class.objects.count() == 0
        assert self.model_class.all.count() == 1

    def test_restore(self):
        self.object.archive()
        assert self.model_class.objects.count() == 0
        assert self.model_class.all.count() == 1
        with patch("haupt.common.workers.send") as workers_send:
            resp = self.client.post(self.url + "restore/")
        assert workers_send.call_count == 0
        assert resp.status_code == status.HTTP_200_OK
        assert self.model_class.objects.count() == 1
        assert self.model_class.all.count() == 1


@pytest.mark.run_mark
class BaseRerunRunApi(BaseTestRunApi):
    def setUp(self):
        super().setUp()
        self.object.delete()
        values = {
            "version": 1.1,
            "kind": "operation",
            "name": "foo",
            "description": "a description",
            "params": {"image": {"value": "foo/bar"}},
            "component": {
                "name": "build-template",
                "inputs": [{"name": "image", "type": "str"}],
                "tags": ["tag1", "tag2"],
                "run": {
                    "kind": V1RunKind.JOB,
                    "container": {"image": "{{ image }}"},
                    "init": [{"connection": "foo", "git": {"revision": "dev"}}],
                },
            },
        }
        op_spec = OperationSpecification.read(values=values)
        self.object = operations.init_and_save_run(
            project_id=self.project.id, op_spec=op_spec, user_id=self.user.id
        )
        self.url = "/{}/{}/{}/runs/{}/".format(
            API_V1, self.user.username, self.project.name, self.object.uuid.hex
        )


@pytest.mark.run_mark
class TestRestartRunViewV1(BaseRerunRunApi):
    serializer_class = RunSerializer

    def test_restart(self):
        data = {}
        assert self.queryset.count() == 1
        with patch("haupt.common.workers.send") as workers_send:
            resp = self.client.post(self.url + "restart/", data)
        assert resp.status_code == status.HTTP_201_CREATED
        assert self.queryset.count() == 2
        assert len(workers_send.call_args_list) == 1
        assert {c[0][0] for c in workers_send.call_args_list} == {
            SchedulerCeleryTasks.RUNS_PREPARE,
        }

        last_experiment = self.queryset.last()
        assert last_experiment.is_clone is True
        assert last_experiment.is_restart is True
        assert last_experiment.is_copy is False
        assert last_experiment.is_resume is False
        assert last_experiment.original == self.object

    def test_restart_patch_config(self):
        data = {"content": '{"trigger": "all_succeeded"}'}
        with patch("haupt.common.workers.send") as workers_send:
            resp = self.client.post(self.url + "restart/", data)
        assert resp.status_code == status.HTTP_201_CREATED
        assert self.queryset.count() == 2
        assert len(workers_send.call_args_list) == 1
        assert {c[0][0] for c in workers_send.call_args_list} == {
            SchedulerCeleryTasks.RUNS_PREPARE,
        }

        last_experiment = self.queryset.last()
        assert last_experiment.is_clone is True
        assert last_experiment.is_restart is True
        assert last_experiment.is_copy is False
        assert last_experiment.is_resume is False
        assert last_experiment.original == self.object

    def test_restart_patch_wrong_config_raises(self):
        data = {"content": "sdf"}
        with patch("haupt.common.workers.send") as workers_send:
            resp = self.client.post(self.url + "restart/", data)

        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert workers_send.call_count == 0
        assert self.queryset.count() == 1

    def test_restart_recompile_override_config_raises(self):
        data = {
            "content": '{"trigger": "all_succeeded"}',
            "meta_info": {META_RECOMPILE: True},
        }
        with patch("haupt.common.workers.send"):
            resp = self.client.post(self.url + "restart/", data)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_restart_recompile_config(self):
        data = {"content": self.object.raw_content, "meta_info": {META_RECOMPILE: True}}
        with patch("haupt.common.workers.send") as workers_send:
            resp = self.client.post(self.url + "restart/", data)
        assert resp.status_code == status.HTTP_201_CREATED
        assert self.queryset.count() == 2
        assert len(workers_send.call_args_list) == 1
        assert {c[0][0] for c in workers_send.call_args_list} == {
            SchedulerCeleryTasks.RUNS_PREPARE,
        }

        last_experiment = self.queryset.last()
        assert last_experiment.is_clone is True
        assert last_experiment.is_restart is True
        assert last_experiment.is_copy is False
        assert last_experiment.is_resume is False
        assert last_experiment.original == self.object


@pytest.mark.run_mark
class TestResumeRunViewV1(BaseRerunRunApi):
    serializer_class = RunSerializer

    def setUp(self):
        super().setUp()
        new_run_status(
            self.object,
            condition=V1StatusCondition.get_condition(
                type=V1Statuses.STOPPED, status=True
            ),
        )

    def test_resume(self):
        data = {}
        assert self.queryset.count() == 1
        with patch("haupt.common.workers.send") as workers_send:
            resp = self.client.post(self.url + "resume/", data)
        assert resp.status_code == status.HTTP_201_CREATED
        assert self.queryset.count() == 1
        assert len(workers_send.call_args_list) == 1
        assert {c[0][0] for c in workers_send.call_args_list} == {
            SchedulerCeleryTasks.RUNS_PREPARE,
        }

        last_experiment = self.queryset.last()
        assert last_experiment.is_clone is False
        assert last_experiment.is_restart is False
        assert last_experiment.is_copy is False
        assert last_experiment.is_resume is True
        assert last_experiment.original is None

    def test_resume_patch_config(self):
        data = {"content": '{"trigger": "all_succeeded"}'}
        with patch("haupt.common.workers.send") as workers_send:
            resp = self.client.post(self.url + "resume/", data)

        assert resp.status_code == status.HTTP_201_CREATED
        assert self.queryset.count() == 1
        assert len(workers_send.call_args_list) == 1
        assert {c[0][0] for c in workers_send.call_args_list} == {
            SchedulerCeleryTasks.RUNS_PREPARE,
        }

        last_experiment = self.queryset.last()
        assert last_experiment.is_clone is False
        assert last_experiment.is_restart is False
        assert last_experiment.is_copy is False
        assert last_experiment.is_resume is True
        assert last_experiment.original is None

    def test_resume_patch_wrong_config_raises(self):
        data = {"content": "d"}
        with patch("haupt.common.workers.send") as workers_send:
            resp = self.client.post(self.url + "resume/", data)

        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert workers_send.call_count == 0
        assert self.queryset.count() == 1

    def test_resume_recompile_override_config_raises(self):
        data = {
            "content": '{"trigger": "all_succeeded"}',
            "meta_info": {META_RECOMPILE: True},
        }
        with patch("haupt.common.workers.send"):
            resp = self.client.post(self.url + "resume/", data)

        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_resume_recompile_config(self):
        data = {"content": self.object.raw_content, "meta_info": {META_RECOMPILE: True}}
        with patch("haupt.common.workers.send") as workers_send:
            resp = self.client.post(self.url + "resume/", data)

        assert resp.status_code == status.HTTP_201_CREATED
        assert self.queryset.count() == 1
        assert len(workers_send.call_args_list) == 1
        assert {c[0][0] for c in workers_send.call_args_list} == {
            SchedulerCeleryTasks.RUNS_PREPARE,
        }

        last_experiment = self.queryset.last()
        assert last_experiment.is_clone is False
        assert last_experiment.is_restart is False
        assert last_experiment.is_copy is False
        assert last_experiment.is_resume is True
        assert last_experiment.original is None

    def test_resume_undone_run(self):
        new_run_status(
            self.object,
            condition=V1StatusCondition.get_condition(
                type=V1Statuses.RUNNING, status=True
            ),
            force=True,
        )
        data = {}
        assert self.queryset.count() == 1
        with patch("haupt.common.workers.send") as workers_send:
            resp = self.client.post(self.url + "resume/", data)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert workers_send.call_count == 0
        assert self.queryset.count() == 1


@pytest.mark.run_mark
class TestCopyRunViewV1(BaseRerunRunApi):
    serializer_class = RunSerializer

    def test_copy(self):
        data = {}
        assert self.queryset.count() == 1
        with patch("haupt.common.workers.send") as workers_send:
            resp = self.client.post(self.url + "copy/", data)
        assert resp.status_code == status.HTTP_201_CREATED
        assert len(workers_send.call_args_list) == 1
        assert {c[0][0] for c in workers_send.call_args_list} == {
            SchedulerCeleryTasks.RUNS_PREPARE,
        }
        assert self.queryset.count() == 2

        last_experiment = self.queryset.last()
        assert last_experiment.is_clone is True
        assert last_experiment.is_restart is False
        assert last_experiment.is_copy is True
        assert last_experiment.is_resume is False
        assert last_experiment.original == self.object

    def test_copy_patch_config(self):
        data = {"content": '{"trigger": "all_succeeded"}'}
        assert self.queryset.count() == 1
        with patch("haupt.common.workers.send") as workers_send:
            resp = self.client.post(self.url + "copy/", data)

        assert resp.status_code == status.HTTP_201_CREATED
        assert len(workers_send.call_args_list) == 1
        assert {c[0][0] for c in workers_send.call_args_list} == {
            SchedulerCeleryTasks.RUNS_PREPARE,
        }
        assert self.queryset.count() == 2

        last_experiment = self.queryset.last()
        assert last_experiment.is_clone is True
        assert last_experiment.is_restart is False
        assert last_experiment.is_copy is True
        assert last_experiment.is_resume is False
        assert last_experiment.original == self.object

    def test_resume_patch_wrong_config_raises(self):
        data = {"content": "sdf"}
        assert self.queryset.count() == 1
        with patch("haupt.common.workers.send") as workers_send:
            resp = self.client.post(self.url + "copy/", data)

        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert workers_send.call_count == 0
        assert self.queryset.count() == 1


@pytest.mark.run_mark
class TestTransferRunViewV1(BaseTestRunApi):
    def setUp(self):
        super().setUp()
        self.same_owner_project = ProjectFactory()

    def test_transfer(self):
        data = {"project": self.same_owner_project.name}
        assert self.queryset.count() == 1
        assert Run.objects.filter(project=self.project).count() == 1
        assert Run.objects.filter(project=self.same_owner_project).count() == 0
        with patch("haupt.common.workers.send") as workers_send:
            resp = self.client.post(self.url + "transfer/", data)
        assert resp.status_code == status.HTTP_200_OK
        assert len(workers_send.call_args_list) == 0
        assert self.queryset.count() == 1
        assert Run.objects.filter(project=self.project).count() == 0
        assert Run.objects.filter(project=self.same_owner_project).count() == 1

    def test_transfer_same_project(self):
        data = {"project": self.project.name}
        assert self.queryset.count() == 1
        assert Run.objects.filter(project=self.project).count() == 1
        assert Run.objects.filter(project=self.same_owner_project).count() == 0
        with patch("haupt.common.workers.send") as workers_send:
            resp = self.client.post(self.url + "transfer/", data)
        assert resp.status_code == status.HTTP_200_OK
        assert workers_send.call_count == 0
        assert len(workers_send.call_args_list) == 0
        assert self.queryset.count() == 1
        assert Run.objects.filter(project=self.project).count() == 1
        assert Run.objects.filter(project=self.same_owner_project).count() == 0


@pytest.mark.run_mark
class TestRunStatusListViewV1(BaseTestRunApi):
    serializer_class = RunStatusSerializer
    num_objects = 3

    def setUp(self):
        super().setUp()
        self.url = self.url + "statuses/"

    def test_get(self):
        resp = self.client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK

        data = resp.data
        assert len(data["status_conditions"]) == 0
        assert data == self.serializer_class(self.object).data

        new_run_status(
            self.object,
            condition=V1StatusCondition.get_condition(
                type=V1Statuses.RUNNING, status=True
            ),
        )
        self.object.refresh_from_db()
        resp = self.client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK

        data = resp.data
        assert len(data["status_conditions"]) == 1
        assert data == self.serializer_class(self.object).data

        new_run_stop_status(run=self.object, message="foo")
        self.object.refresh_from_db()
        resp = self.client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK

        data = resp.data
        assert len(data["status_conditions"]) == 2
        assert data == self.serializer_class(self.object).data

    def test_create(self):
        assert self.object.status == V1Statuses.CREATED
        assert self.object.status_conditions == {}
        data = {}
        resp = self.client.post(self.url, data)
        assert resp.status_code == status.HTTP_201_CREATED
        self.object.refresh_from_db()
        assert self.object.status == V1Statuses.CREATED
        assert self.object.status_conditions == {}

        data = {"condition": {"type": V1Statuses.RUNNING}}
        resp = self.client.post(self.url, data)
        assert resp.status_code == status.HTTP_201_CREATED
        self.object.refresh_from_db()
        assert self.object.status == V1Statuses.RUNNING
        condition = self.object.status_conditions[0]
        condition.pop("last_transition_time")
        condition.pop("last_update_time")
        assert condition == {
            "type": V1Statuses.RUNNING,
        }

        # Create with message and traceback
        data = {
            "condition": {
                "type": V1Statuses.FAILED,
                "status": True,
                "reason": "Run is stopped",
                "message": "foo",
            }
        }
        resp = self.client.post(self.url, data)
        assert resp.status_code == status.HTTP_201_CREATED
        self.object.refresh_from_db()
        assert self.object.status == V1Statuses.FAILED
        assert len(self.object.status_conditions) == 2
        condition = self.object.status_conditions[1]
        condition.pop("last_transition_time")
        condition.pop("last_update_time")
        assert condition == {
            "type": V1Statuses.FAILED,
            "status": True,
            "reason": "Run is stopped",
            "message": "foo",
        }

    def test_final_status(self):
        assert self.object.status == V1Statuses.CREATED
        assert self.object.status_conditions == {}
        # Create with failed status
        data = {
            "condition": {
                "type": V1Statuses.FAILED,
                "status": True,
                "reason": "Run is stopped",
                "message": "foo",
            }
        }
        resp = self.client.post(self.url, data)
        assert resp.status_code == status.HTTP_201_CREATED
        self.object.refresh_from_db()
        assert self.object.status == V1Statuses.FAILED
        assert len(self.object.status_conditions) == 1
        condition = self.object.status_conditions[0]
        condition.pop("last_transition_time")
        condition.pop("last_update_time")
        assert condition == {
            "type": V1Statuses.FAILED,
            "status": True,
            "reason": "Run is stopped",
            "message": "foo",
        }

        # Create with stopped status
        data = {
            "condition": {
                "type": V1Statuses.STOPPED,
            }
        }
        resp = self.client.post(self.url, data)
        assert resp.status_code == status.HTTP_201_CREATED
        self.object.refresh_from_db()
        assert self.object.status == V1Statuses.FAILED
        assert len(self.object.status_conditions) == 1
        condition = self.object.status_conditions[0]
        condition.pop("last_transition_time")
        condition.pop("last_update_time")
        assert condition == {
            "type": V1Statuses.FAILED,
            "status": True,
            "reason": "Run is stopped",
            "message": "foo",
        }

        # Create with stopped status with force flag
        data = {
            "condition": {
                "type": V1Statuses.STOPPED,
            },
            "force": True,
        }
        resp = self.client.post(self.url, data)
        assert resp.status_code == status.HTTP_201_CREATED
        self.object.refresh_from_db()
        assert self.object.status == V1Statuses.STOPPED
        assert len(self.object.status_conditions) == 2
        condition = self.object.status_conditions[1]
        condition.pop("last_transition_time")
        condition.pop("last_update_time")
        assert condition == {
            "type": V1Statuses.STOPPED,
        }


@pytest.mark.run_mark
class TestStopRunViewV1(BaseTestRunApi):
    def setUp(self):
        super().setUp()
        self.url = self.url + "stop/"

    def test_stop_safe_stop(self):
        assert self.queryset.count() == 1
        last_run = self.queryset.last()
        last_run.managed_by = ManagedBy.AGENT
        last_run.save()
        assert self.queryset.last().status == V1Statuses.CREATED
        with patch("haupt.common.workers.send") as workers_send:
            resp = self.client.post(self.url)
        assert resp.status_code == status.HTTP_200_OK
        assert workers_send.call_count == 1
        assert self.queryset.count() == 1
        assert self.queryset.last().status == V1Statuses.STOPPED

    def test_stop(self):
        assert self.queryset.count() == 1
        last_run = self.queryset.last()
        last_run.managed_by = ManagedBy.AGENT
        last_run.status = V1Statuses.QUEUED
        last_run.save()
        with patch("haupt.common.workers.send") as workers_send:
            resp = self.client.post(self.url)
        assert resp.status_code == status.HTTP_200_OK
        assert workers_send.call_count == 0
        assert self.queryset.count() == 1
        assert self.queryset.last().status == V1Statuses.STOPPING

    def test_stop_non_managed(self):
        assert self.queryset.count() == 1
        last_run = self.queryset.last()
        last_run.managed_by = ManagedBy.USER
        last_run.save()
        assert self.queryset.last().status == V1Statuses.CREATED
        with patch("haupt.common.workers.send") as workers_send:
            resp = self.client.post(self.url)
        assert resp.status_code == status.HTTP_200_OK
        assert workers_send.call_count == 1
        assert self.queryset.count() == 1
        assert self.queryset.last().status == V1Statuses.STOPPED


@pytest.mark.run_mark
class TestApproveRunViewV1(BaseTestRunApi):
    def setUp(self):
        super().setUp()
        self.url = self.url + "approve/"

    def test_approve(self):
        assert self.queryset.count() == 1
        last_run = self.queryset.last()
        last_run.pending = V1RunPending.APPROVAL
        last_run.save()
        with patch("haupt.common.workers.send") as workers_send:
            resp = self.client.post(self.url)
        assert resp.status_code == status.HTTP_200_OK
        assert workers_send.call_count == 1
        assert self.queryset.count() == 1
        assert self.queryset.last().pending is None

    def test_approve_compiled(self):
        assert self.queryset.count() == 1
        last_run = self.queryset.last()
        last_run.pending = V1RunPending.APPROVAL
        last_run.status = V1Statuses.COMPILED
        last_run.save()
        with patch("haupt.common.workers.send") as workers_send:
            resp = self.client.post(self.url)
        assert resp.status_code == status.HTTP_200_OK
        assert workers_send.call_count == 1
        assert self.queryset.count() == 1
        assert self.queryset.last().pending is None

    def test_approve_cache(self):
        assert self.queryset.count() == 1
        last_run = self.queryset.last()
        last_run.pending = V1RunPending.CACHE
        last_run.save()
        with patch("haupt.common.workers.send") as workers_send:
            resp = self.client.post(self.url)
        assert resp.status_code == status.HTTP_200_OK
        assert workers_send.call_count == 1
        assert {c[0][0] for c in workers_send.call_args_list} == {
            SchedulerCeleryTasks.RUNS_PREPARE,
        }
        assert self.queryset.count() == 1
        assert self.queryset.last().pending is None

    def test_approve_build(self):
        assert self.queryset.count() == 1
        last_run = self.queryset.last()
        last_run.pending = V1RunPending.BUILD
        last_run.content = None
        last_run.save()
        with patch("haupt.common.workers.send") as workers_send:
            resp = self.client.post(self.url)
        assert resp.status_code == status.HTTP_200_OK
        assert workers_send.call_count == 1
        assert self.queryset.count() == 1
        assert self.queryset.last().pending is None

    def test_approve_build_approve(self):
        assert self.queryset.count() == 1
        last_run = self.queryset.last()
        values = {
            "version": 1.1,
            "kind": "operation",
            "name": "foo",
            "description": "a description",
            "params": {"image": {"value": "foo/bar"}},
            "isApproved": False,
            "component": {
                "name": "build-template",
                "inputs": [{"name": "image", "type": "str"}],
                "tags": ["tag1", "tag2"],
                "run": {
                    "kind": V1RunKind.JOB,
                    "container": {"image": "{{ image }}"},
                    "init": [{"connection": "foo", "git": {"revision": "dev"}}],
                },
            },
        }
        op_spec = OperationSpecification.read(values=values)
        instance = operations.init_run(
            project_id=self.project.id, op_spec=op_spec, user_id=self.user.id
        ).instance
        last_run.content = instance.content
        last_run.pending = V1RunPending.BUILD
        last_run.save()
        with patch("haupt.common.workers.send") as workers_send:
            resp = self.client.post(self.url)
        assert resp.status_code == status.HTTP_200_OK
        assert workers_send.call_count == 1
        assert self.queryset.count() == 1
        assert self.queryset.last().pending == V1RunPending.APPROVAL

    def test_approve_upload(self):
        assert self.queryset.count() == 1
        last_run = self.queryset.last()
        last_run.pending = V1RunPending.UPLOAD
        last_run.content = None
        last_run.save()
        with patch("haupt.common.workers.send") as workers_send:
            resp = self.client.post(self.url)
        assert resp.status_code == status.HTTP_200_OK
        assert workers_send.call_count == 1
        assert self.queryset.count() == 1
        assert self.queryset.last().pending is None

    def test_approve_build_upload(self):
        assert self.queryset.count() == 1
        last_run = self.queryset.last()
        values = {
            "version": 1.1,
            "kind": "operation",
            "name": "foo",
            "description": "a description",
            "params": {"image": {"value": "foo/bar"}},
            "isApproved": False,
            "component": {
                "name": "build-template",
                "inputs": [{"name": "image", "type": "str"}],
                "tags": ["tag1", "tag2"],
                "run": {
                    "kind": V1RunKind.JOB,
                    "container": {"image": "{{ image }}"},
                    "init": [{"connection": "foo", "git": {"revision": "dev"}}],
                },
            },
        }
        op_spec = OperationSpecification.read(values=values)
        instance = operations.init_run(
            project_id=self.project.id, op_spec=op_spec, user_id=self.user.id
        ).instance
        last_run.content = instance.content
        last_run.pending = V1RunPending.UPLOAD
        last_run.save()
        with patch("haupt.common.workers.send") as workers_send:
            resp = self.client.post(self.url)
        assert resp.status_code == status.HTTP_200_OK
        assert workers_send.call_count == 1
        assert self.queryset.count() == 1
        assert self.queryset.last().pending == V1RunPending.APPROVAL

    def test_approve_already_approved_run(self):
        assert self.queryset.count() == 1
        last_run = self.queryset.last()
        last_run.pending = V1RunPending.APPROVAL
        last_run.save()
        resp = self.client.post(self.url)
        assert resp.status_code == status.HTTP_200_OK
        assert self.queryset.count() == 1
        assert self.queryset.last().pending is None

    def test_approve_pipeline_dag_does_not_approve_subtasks(self):
        assert self.queryset.count() == 1
        last_run = self.queryset.last()
        last_run.pending = V1RunPending.APPROVAL
        last_run.kind = V1RunKind.DAG
        last_run.save()
        RunFactory(
            project=self.project,
            user=self.user,
            pipeline=last_run,
            controller=last_run,
            pending=V1RunPending.APPROVAL,
        )
        RunFactory(
            project=self.project, user=self.user, pipeline=last_run, controller=last_run
        )
        RunFactory(project=self.project, user=self.user, controller=last_run)
        with patch("haupt.common.workers.send") as workers_send:
            resp = self.client.post(self.url)
        assert resp.status_code == status.HTTP_200_OK
        assert workers_send.call_count == 1
        assert {c[0][0] for c in workers_send.call_args_list} == {
            SchedulerCeleryTasks.RUNS_PREPARE,
        }
        assert self.queryset.count() == 4
        assert self.queryset.last().pending is None
        assert set(last_run.controller_runs.values_list("pending", flat=True)) == {
            None,
            V1RunPending.APPROVAL,
        }

    def test_approve_pipeline_matrix(self):
        assert self.queryset.count() == 1
        last_run = self.queryset.last()
        last_run.pending = V1RunPending.APPROVAL
        last_run.kind = V1RunKind.MATRIX
        last_run.status = V1Statuses.COMPILED
        last_run.save()
        RunFactory(
            project=self.project,
            user=self.user,
            pipeline=last_run,
            controller=last_run,
            pending=V1RunPending.APPROVAL,
        )
        RunFactory(
            project=self.project, user=self.user, pipeline=last_run, controller=last_run
        )
        RunFactory(project=self.project, user=self.user, controller=last_run)
        with patch("haupt.common.workers.send") as workers_send:
            resp = self.client.post(self.url)
        assert resp.status_code == status.HTTP_200_OK
        assert workers_send.call_count == 1
        assert {c[0][0] for c in workers_send.call_args_list} == {
            SchedulerCeleryTasks.RUNS_START,
        }
        assert self.queryset.count() == 4
        last_run.refresh_from_db()
        assert self.queryset.last().pending is None
        assert set(last_run.controller_runs.values_list("pending", flat=True)) == {
            None,
            V1RunPending.APPROVAL,
        }


@pytest.mark.run_mark
class TestRunBookmarkCreateView(BaseTestBookmarkCreateView):
    model_class = Run
    factory_class = RunFactory

    def get_url(self):
        return "/{}/{}/{}/runs/{}/bookmark/".format(
            API_V1, self.user.username, self.project.name, self.object.uuid.hex
        )

    def create_object(self):
        self.project = ProjectFactory()
        return self.factory_class(user=self.user, project=self.project)


@pytest.mark.run_mark
class TestRunBookmarkDeleteView(BaseTestBookmarkDeleteView):
    model_class = Run
    factory_class = RunFactory

    def get_url(self):
        return "/{}/{}/{}/runs/{}/unbookmark/".format(
            API_V1, self.user.username, self.project.name, self.object.uuid.hex
        )

    def create_object(self):
        self.project = ProjectFactory()
        return self.factory_class(user=self.user, project=self.project)


del BaseTestBookmarkCreateView
del BaseTestBookmarkDeleteView
