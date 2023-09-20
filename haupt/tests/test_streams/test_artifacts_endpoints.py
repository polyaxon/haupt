import os
import pytest

from clipped.utils.paths import create_path

from polyaxon import settings
from polyaxon._utils.test_utils import create_tmp_files, set_store
from polyaxon.api import STREAMS_V1_LOCATION
from tests.base.case import BaseTest


@pytest.mark.artifacts_mark
class TestArtifactsEndpoints(BaseTest):
    def setUp(self):
        super().setUp()
        self.store_root = set_store()
        self.run_path = os.path.join(self.store_root, "uuid")
        # Create run artifacts path and some files
        create_path(self.run_path)
        create_tmp_files(self.run_path)

        self.base_url = (
            STREAMS_V1_LOCATION + "namespace/owner/project/runs/uuid/artifacts"
        )

    def test_download_artifacts(self):
        filepath = os.path.join(settings.CLIENT_CONFIG.archives_root, "uuid.tar.gz")
        assert os.path.exists(filepath) is False
        response = self.client.get(self.base_url)
        assert response.status_code == 200
        assert os.path.exists(filepath) is True
        assert response.headers["Content-Type"] == ""
        assert response.headers["X-Accel-Redirect"] == filepath
        assert response.headers[
            "Content-Disposition"
        ] == 'attachment; filename="{}"'.format("uuid.tar.gz")

    def test_delete_artifacts(self):
        # Created nested path
        nested_path = os.path.join(self.run_path, "foo")
        create_path(nested_path)
        create_tmp_files(nested_path)
        subpath = os.path.join(self.run_path, "foo")

        assert os.path.exists(self.run_path) is True
        assert os.path.exists(subpath) is True
        response = self.client.delete(self.base_url + "?path=foo")
        assert response.status_code == 204
        assert os.path.exists(self.run_path) is True
        assert os.path.exists(subpath) is False

        response = self.client.delete(self.base_url)
        assert response.status_code == 204
        assert os.path.exists(self.run_path) is False
