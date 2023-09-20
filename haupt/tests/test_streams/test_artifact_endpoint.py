import os
import pytest
import shutil

from clipped.utils.paths import create_path

from polyaxon import settings
from polyaxon._utils.test_utils import create_tmp_files, set_store
from polyaxon.api import STREAMS_V1_LOCATION
from tests.base.case import BaseTest


@pytest.mark.artifacts_mark
class TestArtifactEndpoints(BaseTest):
    def setUp(self):
        super().setUp()
        self.store_root = set_store()
        self.run_path = os.path.join(self.store_root, "uuid")
        # Create run artifacts path and some files
        create_path(self.run_path)
        create_tmp_files(self.run_path)
        # Archive path
        self.archive_run_path = os.path.join(
            settings.CLIENT_CONFIG.archives_root, "uuid"
        )

        self.base_url = (
            STREAMS_V1_LOCATION + "namespace/owner/project/runs/uuid/artifact"
        )

    def test_download_artifact_not_passing_path(self):
        response = self.client.get(self.base_url)
        assert response.status_code == 400

    def test_stream_artifact_not_passing_path(self):
        response = self.client.get(self.base_url + "?=stream=true")
        assert response.status_code == 400

    def test_delete_artifact_not_passing_path(self):
        response = self.client.delete(self.base_url)
        assert response.status_code == 400

    def test_download_artifact_non_existing_path(self):
        response = self.client.get(self.base_url + "?path=foo")
        assert response.status_code == 404

    def test_delete_artifact_non_existing_path(self):
        response = self.client.delete(self.base_url + "?path=foo")
        assert response.status_code == 400

    def test_stream_artifact_non_existing_path(self):
        response = self.client.get(self.base_url + "?stream=true&path=foo")
        assert response.status_code == 404

    def test_download_artifact_passing_path(self):
        filepath = os.path.join(self.archive_run_path, "file1.txt")
        assert os.path.exists(filepath) is False
        response = self.client.get(self.base_url + "?path=file1.txt")
        assert response.status_code == 200
        assert os.path.exists(filepath) is True
        assert response.headers["Content-Type"] == ""
        assert response.headers["X-Accel-Redirect"] == os.path.join(
            self.archive_run_path, "file1.txt"
        )
        assert response.headers[
            "Content-Disposition"
        ] == 'attachment; filename="{}"'.format("file1.txt")

        # Nested dirs
        nested_path = os.path.join(self.run_path, "foo")
        create_path(nested_path)
        create_tmp_files(nested_path)
        filepath = os.path.join(self.archive_run_path, "foo", "file1.txt")
        assert os.path.exists(filepath) is False
        response = self.client.get(self.base_url + "?path=foo/file1.txt")
        assert response.status_code == 200
        assert os.path.exists(filepath) is True
        assert response.headers["Content-Type"] == ""
        assert response.headers["X-Accel-Redirect"] == os.path.join(
            self.archive_run_path, "foo/file1.txt"
        )
        assert response.headers[
            "Content-Disposition"
        ] == 'attachment; filename="{}"'.format("file1.txt")

        # The file is cached
        shutil.rmtree(self.run_path)
        response = self.client.get(self.base_url + "?path=foo/file1.txt")
        assert response.status_code == 200
        assert response.headers["X-Accel-Redirect"] == os.path.join(
            self.archive_run_path, "foo/file1.txt"
        )

        # Remove the cached should raise
        shutil.rmtree(os.path.join(self.archive_run_path, "foo"))
        response = self.client.get(self.base_url + "?stream=true&path=foo/file1.txt")
        assert response.status_code == 404

    def test_download_artifact_passing_path_with_force(self):
        # Nested dirs
        nested_path = os.path.join(self.run_path, "foo")
        create_path(nested_path)
        create_tmp_files(nested_path)
        filepath = os.path.join(self.archive_run_path, "foo", "file1.txt")
        assert os.path.exists(filepath) is False
        response = self.client.get(self.base_url + "?path=foo/file1.txt")
        assert response.status_code == 200
        assert os.path.exists(filepath) is True
        assert response.headers["Content-Type"] == ""
        assert response.headers["X-Accel-Redirect"] == os.path.join(
            self.archive_run_path, "foo/file1.txt"
        )
        assert response.headers[
            "Content-Disposition"
        ] == 'attachment; filename="{}"'.format("file1.txt")

        # The file is cached but we force check
        shutil.rmtree(self.run_path)
        response = self.client.get(self.base_url + "?path=foo/file1.txt&force=true")
        assert response.status_code == 404

    def test_stream_artifact_passing_path(self):
        filepath = os.path.join(self.archive_run_path, "file1.txt")
        assert os.path.exists(filepath) is False
        response = self.client.get(self.base_url + "?stream=true&path=file1.txt")
        assert response.status_code == 200
        assert os.path.exists(filepath) is True
        assert response.headers["Content-Type"] == "text/plain"
        assert response.headers["content-length"] == "0"
        assert response.headers["last-modified"] is not None
        assert response.headers["etag"] is not None

        # Nested dirs
        nested_path = os.path.join(self.run_path, "foo")
        create_path(nested_path)
        create_tmp_files(nested_path)
        filepath = os.path.join(self.archive_run_path, "foo", "file1.txt")
        assert os.path.exists(filepath) is False
        response = self.client.get(self.base_url + "?stream=true&path=foo/file1.txt")
        assert response.status_code == 200
        assert os.path.exists(filepath) is True
        assert response.headers["Content-Type"] == "text/plain"
        assert response.headers["content-length"] == "0"
        assert response.headers["last-modified"] is not None
        assert response.headers["etag"] is not None

        # The file is cached
        shutil.rmtree(self.run_path)
        assert os.path.exists(filepath) is True
        response = self.client.get(self.base_url + "?stream=true&path=foo/file1.txt")
        assert response.status_code == 200
        assert os.path.exists(filepath) is True

        # Remove the cached should raise
        shutil.rmtree(os.path.join(self.archive_run_path, "foo"))
        assert os.path.exists(filepath) is False
        response = self.client.get(self.base_url + "?stream=true&path=foo/file1.txt")
        assert response.status_code == 404
        assert os.path.exists(filepath) is False

    def test_stream_artifact_passing_path_with_force(self):
        # Nested dirs
        nested_path = os.path.join(self.run_path, "foo")
        create_path(nested_path)
        create_tmp_files(nested_path)
        filepath = os.path.join(self.archive_run_path, "foo", "file1.txt")
        assert os.path.exists(filepath) is False
        response = self.client.get(self.base_url + "?stream=true&path=foo/file1.txt")
        assert response.status_code == 200
        assert os.path.exists(filepath) is True
        assert response.headers["Content-Type"] == "text/plain"
        assert response.headers["content-length"] == "0"
        assert response.headers["last-modified"] is not None
        assert response.headers["etag"] is not None

        # The file is cached but we force check
        shutil.rmtree(self.run_path)
        assert os.path.exists(filepath) is True
        response = self.client.get(
            self.base_url + "?stream=true&path=foo/file1.txt&force=true"
        )
        assert response.status_code == 404

    def test_delete_artifact_passing_path(self):
        filepath = os.path.join(self.run_path, "file1.txt")
        assert os.path.exists(filepath) is True
        response = self.client.delete(self.base_url + "?path=file1.txt")
        assert response.status_code == 204
        assert os.path.exists(filepath) is False

        # Nested dirs
        nested_path = os.path.join(self.run_path, "foo")
        create_path(nested_path)
        create_tmp_files(nested_path)
        filepath = os.path.join(self.run_path, "foo", "file1.txt")
        assert os.path.exists(filepath) is True
        response = self.client.delete(self.base_url + "?path=foo/file1.txt")
        assert response.status_code == 204
        assert os.path.exists(filepath) is False

        # Deleting same file
        response = self.client.delete(self.base_url + "?path=foo/file1.txt")
        assert response.status_code == 400
