import os
import tempfile


def pytest_configure():
    os.environ["POLYAXON_NO_CONFIG"] = "true"
    os.environ["POLYAXON_CONTEXT_ROOT"] = tempfile.mkdtemp()
    os.environ["POLYAXON_OFFLINE_ROOT"] = tempfile.mkdtemp()
    os.environ["POLYAXON_ARTIFACTS_ROOT"] = tempfile.mkdtemp()
