import os
import pytest
import tempfile
from types import SimpleNamespace

from polyaxon._k8s.manager.async_manager import AsyncK8sManager


def pytest_configure():
    os.environ["POLYAXON_NO_CONFIG"] = "true"
    os.environ["POLYAXON_CONTEXT_ROOT"] = tempfile.mkdtemp()
    os.environ["POLYAXON_OFFLINE_ROOT"] = tempfile.mkdtemp()
    os.environ["POLYAXON_ARTIFACTS_ROOT"] = tempfile.mkdtemp()


@pytest.fixture
def run_pods(monkeypatch):
    # Live pods as (name, run uuid label, containers)
    state = {"pods": [("pod", "uuid", ["main"])]}

    async def setup(self, k8s_config=None):
        pass

    async def get_pod(self, name, reraise=False, namespace=None):
        for pod_name, run_uuid, containers in state["pods"]:
            if pod_name == name:
                return SimpleNamespace(
                    metadata=SimpleNamespace(
                        name=pod_name,
                        namespace=self.namespace,
                        labels={"app.kubernetes.io/instance": run_uuid},
                    ),
                    spec=SimpleNamespace(
                        containers=[SimpleNamespace(name=c) for c in containers]
                    ),
                )

    monkeypatch.setattr(AsyncK8sManager, "setup", setup)
    monkeypatch.setattr(AsyncK8sManager, "get_pod", get_pod)
    return state
