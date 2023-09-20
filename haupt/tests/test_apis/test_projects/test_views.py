import pytest

from flaky import flaky
from mock.mock import patch

from rest_framework import status

from haupt.apis.serializers.projects import (
    BookmarkedProjectSerializer,
    ProjectDetailSerializer,
    ProjectNameSerializer,
    ProjectSerializer,
)
from haupt.db.factories.projects import ProjectFactory
from haupt.db.factories.runs import RunFactory
from haupt.db.managers.live_state import archive_project, restore_project
from haupt.db.models.bookmarks import Bookmark
from haupt.db.models.projects import Project
from haupt.db.models.runs import Run
from polyaxon.api import API_V1
from polyaxon.schemas import LifeCycle, LiveState, V1Statuses
from tests.base.case import (
    BaseTest,
    BaseTestBookmarkCreateView,
    BaseTestBookmarkDeleteView,
)
from tests.test_apis.test_projects.base import BaseTestProjectApi


@pytest.mark.projects_mark
class TestProjectCreateViewV1(BaseTest):
    serializer_class = ProjectSerializer
    model_class = Project
    factory_class = ProjectFactory

    def setUp(self):
        super().setUp()
        self.url = self.get_url()

    def get_url(self):
        return "/{}/polyaxon/projects/create".format(API_V1)

    def test_create(self):
        num_objects = self.model_class.objects.count()
        data = {}
        resp = self.client.post(self.url, data)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        data = {"name": "new_project"}

        resp = self.client.post(self.url, data)
        assert resp.status_code == status.HTTP_201_CREATED
        assert self.model_class.objects.count() == num_objects + 1
        last_obj = self.model_class.objects.last()
        assert last_obj.name == "new_project"


@pytest.mark.projects_mark
class TestProjectListViewV1(BaseTest):
    serializer_class = BookmarkedProjectSerializer
    model_class = Project
    factory_class = ProjectFactory
    num_objects = 3

    def setUp(self):
        super().setUp()
        self.url = "/{}/{}/projects/list/".format(API_V1, self.user.username)
        self.objects = [self.factory_class() for _ in range(self.num_objects)]
        self.queryset = self.model_class.objects.filter().order_by("-updated_at")

    def test_get(self):
        resp = self.client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK

        assert resp.data["next"] is None
        assert resp.data["count"] == len(self.objects)

        data = resp.data["results"]
        assert len(data) == self.queryset.count()
        assert data == self.serializer_class(self.queryset, many=True).data

    def test_get_with_bookmarked_objects(self):
        resp = self.client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK
        self.assertEqual(
            len([1 for obj in resp.data["results"] if obj["bookmarked"] is True]), 0
        )

        # Authenticated user bookmark
        Bookmark.objects.create(content_object=self.objects[0])

        resp = self.client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK
        assert (
            len([1 for obj in resp.data["results"] if obj["bookmarked"] is True]) == 1
        )

    @flaky(max_runs=3)
    def test_pagination(self):
        limit = self.num_objects - 1
        resp = self.client.get("{}?limit={}".format(self.url, limit))
        assert resp.status_code == status.HTTP_200_OK

        next_page = resp.data.get("next")
        assert next_page is not None
        assert resp.data["count"] == self.queryset.count()

        data = resp.data["results"]
        assert len(data) == limit
        assert data == self.serializer_class(self.queryset[:limit], many=True).data

        resp = self.client.get(next_page)
        assert resp.status_code == status.HTTP_200_OK

        assert resp.data["next"] is None

        data = resp.data["results"]
        assert len(data) == 1
        assert data == self.serializer_class(self.queryset[limit:], many=True).data

    def test_get_order_pagination(self):
        queryset = self.queryset.order_by("created_at", "updated_at")
        limit = self.num_objects - 1
        resp = self.client.get(
            "{}?limit={}&{}".format(self.url, limit, "sort=created_at,updated_at")
        )
        assert resp.status_code == status.HTTP_200_OK

        next_page = resp.data.get("next")
        assert next_page is not None
        assert resp.data["count"] == queryset.count()

        data = resp.data["results"]
        assert len(data) == limit
        assert data == self.serializer_class(queryset[:limit], many=True).data

        resp = self.client.get(next_page)
        assert resp.status_code == status.HTTP_200_OK

        assert resp.data["next"] is None

        data = resp.data["results"]
        assert len(data) == 1
        assert data == self.serializer_class(queryset[limit:], many=True).data

    @pytest.mark.filterwarnings("ignore::RuntimeWarning")
    def test_get_filter(self):  # pylint:disable=too-many-statements
        # Wrong filter raises
        resp = self.client.get(self.url + "?query=created_at<2010-01-01")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

        resp = self.client.get(self.url + "?query=created_at:<2010-01-01")
        assert resp.status_code == status.HTTP_200_OK

        assert resp.data["next"] is None
        assert resp.data["count"] == 0

        resp = self.client.get(self.url + "?query=created_at:>=2010-01-01,name:bobobob")
        assert resp.status_code == status.HTTP_200_OK

        assert resp.data["next"] is None
        assert resp.data["count"] == 0

        resp = self.client.get(
            self.url
            + "?query=created_at:>=2010-01-01,name:{}".format(
                "|".join([p.name for p in self.objects])
            )
        )
        assert resp.status_code == status.HTTP_200_OK

        assert resp.data["next"] is None
        assert resp.data["count"] == len(self.objects)

        data = resp.data["results"]
        assert len(data) == self.queryset.count()
        assert data == self.serializer_class(self.queryset, many=True).data

        # Id
        resp = self.client.get(
            self.url
            + "?query=id:{}|{}".format(
                self.objects[0].uuid.hex, self.objects[1].uuid.hex
            )
        )
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["next"] is None
        assert resp.data["count"] == 2

        # Name
        self.objects[0].name = "exp_foo"
        self.objects[0].save()

        resp = self.client.get(self.url + "?query=name:exp_foo")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["next"] is None
        assert resp.data["count"] == 1

        # Name Regex
        resp = self.client.get(self.url + "?query=name:%foo")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["next"] is None
        assert resp.data["count"] == 1

        resp = self.client.get(self.url + "?query=name:{}".format(self.objects[0].name))
        assert resp.data["next"] is None
        assert resp.data["count"] == 1

        # Bookmarks
        resp = self.client.get(self.url + "?bookmarks=1")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["next"] is None
        assert resp.data["count"] == 0

        resp = self.client.get(self.url + "?bookmarks=0")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["next"] is None
        assert resp.data["count"] == 3

        # Adding bookmarks
        Bookmark.objects.create(content_object=self.objects[0])
        Bookmark.objects.create(content_object=self.objects[1])

        # Bookmarks
        resp = self.client.get(self.url + "?bookmarks=1")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["next"] is None
        assert resp.data["count"] == 2

        resp = self.client.get(self.url + "?bookmarks=0")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["next"] is None
        assert resp.data["count"] == 1

        # Bookmarks with filters
        resp = self.client.get(self.url + "?bookmarks=1&query=name:exp_foo")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["next"] is None
        assert resp.data["count"] == 1

        resp = self.client.get(self.url + "?bookmarks=0&query=name:exp_foo")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["next"] is None
        assert resp.data["count"] == 0

        # Archived
        resp = self.client.get(self.url + "?query=live_state:0")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["next"] is None
        assert resp.data["count"] == 0

        archive_project(self.objects[0])

        resp = self.client.get(self.url + "?query=live_state:0")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["next"] is None
        assert resp.data["count"] == 1

        resp = self.client.get(self.url + "?query=live_state:1")
        assert resp.data["next"] is None
        assert resp.data["count"] == len(self.objects) - 1

        restore_project(self.objects[0])

        resp = self.client.get(self.url + "?query=live_state:0")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["next"] is None
        assert resp.data["count"] == 0

        resp = self.client.get(self.url + "?query=live_state:1")
        assert resp.data["next"] is None
        assert resp.data["count"] == len(self.objects)

        # Schedule immediate deletion
        resp = self.client.get(self.url + "?query=live_state:0")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["next"] is None
        assert resp.data["count"] == 0

        archive_project(self.objects[0])

        resp = self.client.get(self.url + "?query=live_state:0")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["next"] is None
        assert resp.data["count"] == 1

        resp = self.client.get(self.url + "?query=live_state:1")
        assert resp.data["next"] is None
        assert resp.data["count"] == len(self.objects) - 1

        restore_project(self.objects[0])

        resp = self.client.get(self.url + "?query=live_state:0")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["next"] is None
        assert resp.data["count"] == 0

        resp = self.client.get(self.url + "?query=live_state:1")
        assert resp.data["next"] is None
        assert resp.data["count"] == len(self.objects)


@pytest.mark.projects_mark
class TestProjectNameListViewV1(BaseTest):
    serializer_class = ProjectNameSerializer
    model_class = Project
    factory_class = ProjectFactory
    num_objects = 3

    def setUp(self):
        super().setUp()
        self.url = "/{}/{}/projects/names/".format(API_V1, self.user.username)
        self.objects = [self.factory_class() for _ in range(self.num_objects)]
        self.queryset = self.model_class.objects.filter()
        self.queryset = self.queryset.order_by("-updated_at")

    def test_get(self):
        resp = self.client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK

        assert resp.data["next"] is None
        assert resp.data["count"] == len(self.objects)

        data = resp.data["results"]
        assert len(data) == self.queryset.count()
        assert data == self.serializer_class(self.queryset, many=True).data

    @flaky(max_runs=3)
    def test_pagination(self):
        limit = self.num_objects - 1
        resp = self.client.get("{}?limit={}".format(self.url, limit))
        assert resp.status_code == status.HTTP_200_OK

        next_page = resp.data.get("next")
        assert next_page is not None
        assert resp.data["count"] == self.queryset.count()

        data = resp.data["results"]
        assert len(data) == limit
        assert data == self.serializer_class(self.queryset[:limit], many=True).data

        resp = self.client.get(next_page)
        assert resp.status_code == status.HTTP_200_OK

        assert resp.data["next"] is None

        data = resp.data["results"]
        assert len(data) == 1
        assert data == self.serializer_class(self.queryset[limit:], many=True).data


@pytest.mark.projects_mark
class TestProjectDetailViewV1(BaseTestProjectApi):
    serializer_class = ProjectDetailSerializer

    def test_get(self):
        resp = self.client.get(self.url)
        assert resp.status_code == status.HTTP_200_OK
        expected = self.serializer_class(self.object_query).data
        assert resp.data == expected

    def test_patch(self):
        new_tags = ["foo", "bar"]
        new_desc = "foo bar"
        data = {"tags": new_tags, "description": new_desc}
        assert self.project.tags != data["tags"]
        assert self.project.description != new_desc
        resp = self.client.patch(self.url, data=data)
        assert resp.status_code == status.HTTP_200_OK

        new_object = self.model_class.objects.get(id=self.project.id)
        assert new_object.description != self.project.description
        assert new_object.description == new_desc
        assert new_object.tags != self.project.tags
        assert set(new_object.tags) == set(new_tags)
        assert new_object.runs.count() == 2

        new_name = "updated_project_name"
        data = {"name": new_name}
        assert self.project.name != data["name"]
        resp = self.client.patch(self.url, data=data)
        assert resp.status_code == status.HTTP_200_OK

        new_object = self.model_class.objects.get(id=self.project.id)
        assert new_object.name != self.project.name
        assert new_object.name == new_name
        assert new_object.runs.count() == 2

    def test_delete(self):
        for _ in range(2):
            run = RunFactory(project=self.project, user=self.user)
            run.status = V1Statuses.RUNNING
            run.save()

        assert self.queryset.count() == 1
        assert Run.objects.count() == 4

        resp = self.client.delete(self.url)

        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert self.queryset.count() == 0
        assert Project.all.count() == 1  # Async
        assert Project.all.last().live_state == LiveState.DELETION_PROGRESSING
        assert Run.objects.count() == 0
        assert Run.all.count() == 4
        assert set(Run.all.values_list("live_state", flat=True)) == {
            LiveState.DELETION_PROGRESSING
        }


@pytest.mark.projects_mark
class TestProjectArchiveRestoreViewV1(BaseTestProjectApi):
    def test_archive_schedules_run_archive(self):
        for _ in range(2):
            RunFactory(project=self.project, user=self.user)

        assert (
            Run.all.exclude(status__in=LifeCycle.DONE_OR_IN_PROGRESS_VALUES).count()
            == 4
        )
        assert self.queryset.count() == 1
        assert Run.objects.count() == 4

        resp = self.client.post(self.url + "archive/")

        assert resp.status_code == status.HTTP_200_OK
        assert self.queryset.count() == 0
        assert Run.objects.count() == 0
        assert Run.all.count() == 4  # Async
        assert (
            Run.all.exclude(status__in=LifeCycle.DONE_OR_IN_PROGRESS_VALUES).count()
            == 0
        )
        assert set(Run.all.values_list("live_state", flat=True)) == {LiveState.ARCHIVED}

    def test_restore_schedules_deletion(self):
        for _ in range(2):
            RunFactory(project=self.project, user=self.user)

        archive_project(self.project)

        assert self.queryset.count() == 0
        assert Project.all.count() == 1
        assert Run.objects.count() == 0
        assert Run.all.count() == 4

        resp = self.client.post(self.url + "restore/")

        assert resp.status_code == status.HTTP_200_OK
        assert self.queryset.count() == 1
        assert Project.all.count() == 1
        assert Run.objects.count() == 4


@pytest.mark.projects_mark
class TestProjectBookmarkCreateView(BaseTestBookmarkCreateView):
    model_class = Project
    factory_class = ProjectFactory

    def get_url(self):
        return "/{}/{}/{}/bookmark/".format(
            API_V1, self.user.username, self.object.name
        )

    def create_object(self):
        return self.factory_class()


@pytest.mark.projects_mark
class TestProjectBookmarkDeleteView(BaseTestBookmarkDeleteView):
    model_class = Project
    factory_class = ProjectFactory

    def get_url(self):
        return "/{}/{}/{}/unbookmark/".format(
            API_V1, self.user.username, self.object.name
        )

    def create_object(self):
        return self.factory_class()


del BaseTestBookmarkCreateView
del BaseTestBookmarkDeleteView
