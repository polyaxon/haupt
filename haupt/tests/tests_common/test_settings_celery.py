from unittest import TestCase

from haupt.common.settings.celery import set_celery
from haupt.schemas.platform_config import PlatformConfig
from polyaxon._config.reader import ConfigReader


class TestSetCelery(TestCase):
    @staticmethod
    def get_context(publisher: bool = False, **config_values) -> dict:
        # No `os.environ`: container test runs set `POLYAXON_BROKER_BACKEND`.
        config = ConfigReader.read_configs(
            [
                "./tests/tests_common/fixtures_static/configs/non_opt_config_tests.json",
                {"POLYAXON_ENVIRONMENT": "testing", **config_values},
            ]
        )
        context = {}
        set_celery(
            context=context,
            config=PlatformConfig.from_dict(config.data),
            routes={},
            publisher=publisher,
        )
        return context

    def test_publisher_bounds_redis_broker_sockets(self):
        context = self.get_context(
            publisher=True,
            POLYAXON_BROKER_BACKEND="redis",
            POLYAXON_REDIS_CELERY_BROKER_URL="localhost:6379/0",
        )
        assert context["CELERY_BROKER_TRANSPORT_OPTIONS"] == {
            "socket_connect_timeout": 5,
            "socket_timeout": 5,
        }

    def test_worker_keeps_broker_defaults(self):
        context = self.get_context(
            POLYAXON_BROKER_BACKEND="redis",
            POLYAXON_REDIS_CELERY_BROKER_URL="localhost:6379/0",
        )
        assert "CELERY_BROKER_TRANSPORT_OPTIONS" not in context

    def test_publisher_without_redis_broker_keeps_defaults(self):
        context = self.get_context(publisher=True)
        assert "CELERY_BROKER_TRANSPORT_OPTIONS" not in context
