import os
import pytest

from clipped.utils.paths import create_path

from polyaxon._utils.test_utils import create_tmp_files, set_store
from polyaxon.api import STREAMS_V1_LOCATION
from tests.base.case import BaseTest


@pytest.mark.artifacts_mark
class TestArtifactsTreeEndpoints(BaseTest):
    def setUp(self):
        super().setUp()
        self.store_root = set_store()
        self.run_path = os.path.join(self.store_root, "uuid")
        # Create run artifacts path and some files
        create_path(self.run_path)
        create_tmp_files(self.run_path)

        self.base_url = (
            STREAMS_V1_LOCATION + "namespace/owner/project/runs/uuid/artifacts/tree"
        )

    def test_get_artifacts_tree_non_existing_path(self):
        response = self.client.get(self.base_url + "?path=foo")
        assert response.status_code == 200
        results = response.json()
        assert results.pop("error") is not None
        assert results == {"dirs": [], "files": {}}

    def test_get_artifacts_tree(self):
        response = self.client.get(self.base_url)
        assert response.status_code == 200
        assert response.json() == {
            "dirs": [],
            "files": {"file0.txt": 0, "file1.txt": 0, "file2.txt": 0, "file3.txt": 0},
        }

        # add nested
        nested_path = os.path.join(self.run_path, "foo")
        create_path(nested_path)
        create_tmp_files(nested_path)

        response = self.client.get(self.base_url)
        assert response.status_code == 200
        assert response.json() == {
            "dirs": ["foo"],
            "files": {"file0.txt": 0, "file1.txt": 0, "file2.txt": 0, "file3.txt": 0},
        }

        response = self.client.get(self.base_url + "?path=foo")
        assert response.status_code == 200
        assert response.json() == {
            "dirs": [],
            "files": {"file0.txt": 0, "file1.txt": 0, "file2.txt": 0, "file3.txt": 0},
        }

        response = self.client.get(self.base_url + "?path=foo/file1.txt")
        assert response.status_code == 200
        results = response.json()
        assert results.pop("error") is not None
        assert results == {"dirs": [], "files": {}}
