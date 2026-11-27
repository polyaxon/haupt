import pytest

from haupt.schemas.platform_config import PlatformConfig
from haupt.schemas.proxies_config import ProxiesConfig
from polyaxon._utils.test_utils import BaseTestCase


BASE_MODEL_CONFIG = {
    "populate_by_name": True,
    "validate_assignment": True,
    "arbitrary_types_allowed": True,
    "use_enum_values": True,
    "ser_json_timedelta": "float",
    "protected_namespaces": (),
}


@pytest.mark.schemas_mark
class TestModelConfig(BaseTestCase):
    def test_schema_model_config(self):
        for cls in (PlatformConfig, ProxiesConfig):
            with self.subTest(cls=cls.__name__):
                expected = {**BASE_MODEL_CONFIG, "extra": "ignore"}
                assert {k: cls.model_config.get(k) for k in expected} == expected
                assert "Config" not in vars(cls)
