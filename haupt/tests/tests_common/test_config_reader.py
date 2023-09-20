import os

from unittest import TestCase

from haupt.schemas.platform_config import PlatformConfig
from polyaxon._config.reader import ConfigReader


class TestConfigReader(TestCase):
    def test_get_from_os_env(self):
        os.environ["POLYAXON_ENVIRONMENT"] = "testing"
        os.environ["FOO_BAR_KEY"] = "foo_bar"
        config = ConfigReader.read_configs(
            [
                os.environ,
                "./tests/tests_common/fixtures_static/configs/non_opt_config_tests.json",
            ]
        )
        config = PlatformConfig.from_dict(config.data)
        assert config.env == "testing"

    def test_get_broker(self):
        os.environ["POLYAXON_ENVIRONMENT"] = "testing"
        os.environ.pop("POLYAXON_BROKER_BACKEND", None)
        config = ConfigReader.read_configs(
            [
                os.environ,
                "./tests/tests_common/fixtures_static/configs/non_opt_config_tests.json",
            ]
        )
        config = PlatformConfig.from_dict(config.data)
        assert config.broker_backend is None
        assert config.is_redis_broker is False
        assert config.is_rabbitmq_broker is False

        os.environ["POLYAXON_ENVIRONMENT"] = "testing"
        os.environ.pop("POLYAXON_BROKER_BACKEND", None)
        config = ConfigReader.read_configs(
            [
                os.environ,
                "./tests/tests_common/fixtures_static/configs/non_opt_config_tests.json",
                {"POLYAXON_BROKER_BACKEND": "rabbitmq"},
            ]
        )
        config = PlatformConfig.from_dict(config.data)
        assert config.broker_backend == "rabbitmq"
        assert config.is_redis_broker is False
        assert config.is_rabbitmq_broker is True

        config = ConfigReader.read_configs(
            [
                os.environ,
                "./tests/tests_common/fixtures_static/configs/non_opt_config_tests.json",
                {"POLYAXON_BROKER_BACKEND": "redis"},
            ]
        )
        config = PlatformConfig.from_dict(config.data)
        assert config.broker_backend == "redis"
        assert config.is_redis_broker is True
        assert config.is_rabbitmq_broker is False

    def test_get_broker_url(self):
        os.environ["POLYAXON_ENVIRONMENT"] = "testing"
        os.environ.pop("POLYAXON_RABBITMQ_USER", None)
        os.environ.pop("POLYAXON_RABBITMQ_PASSWORD", None)
        config = ConfigReader.read_configs(
            [
                os.environ,
                "./tests/tests_common/fixtures_static/configs/non_opt_config_tests.json",
                {
                    "POLYAXON_BROKER_BACKEND": "redis",
                    "POLYAXON_REDIS_CELERY_BROKER_URL": "foo",
                },
            ]
        )
        config = PlatformConfig.from_dict(config.data)
        assert config.get_broker_url() == "redis://foo"

        config = ConfigReader.read_configs(
            [
                os.environ,
                "./tests/tests_common/fixtures_static/configs/non_opt_config_tests.json",
                {
                    "POLYAXON_REDIS_PROTOCOL": "rediss",
                    "POLYAXON_BROKER_BACKEND": "redis",
                    "POLYAXON_REDIS_CELERY_BROKER_URL": "foo",
                },
            ]
        )
        config = PlatformConfig.from_dict(config.data)
        assert config.get_broker_url() == "rediss://foo"

        config = ConfigReader.read_configs(
            [
                os.environ,
                "./tests/tests_common/fixtures_static/configs/non_opt_config_tests.json",
                {
                    "POLYAXON_BROKER_BACKEND": "redis",
                    "POLYAXON_REDIS_CELERY_BROKER_URL": "foo",
                    "POLYAXON_REDIS_PASSWORD": "pass",
                },
            ]
        )
        config = PlatformConfig.from_dict(config.data)
        assert config.get_broker_url() == "redis://:pass@foo"

        config = ConfigReader.read_configs(
            [
                os.environ,
                "./tests/tests_common/fixtures_static/configs/non_opt_config_tests.json",
                {
                    "POLYAXON_AMQP_URL": "foo",
                    "POLYAXON_BROKER_BACKEND": "rabbitmq",
                    "POLYAXON_REDIS_CELERY_BROKER_URL": "foo",
                },
            ]
        )
        config = PlatformConfig.from_dict(config.data)
        assert config.get_broker_url() == "amqp://foo"

        config = ConfigReader.read_configs(
            [
                os.environ,
                "./tests/tests_common/fixtures_static/configs/non_opt_config_tests.json",
                {
                    "POLYAXON_AMQP_URL": "foo",
                    "POLYAXON_BROKER_BACKEND": "rabbitmq",
                    "POLYAXON_RABBITMQ_PASSWORD": "",
                    "POLYAXON_REDIS_CELERY_BROKER_URL": "foo",
                },
            ]
        )
        config = PlatformConfig.from_dict(config.data)
        assert config.get_broker_url() == "amqp://foo"

        config = ConfigReader.read_configs(
            [
                os.environ,
                "./tests/tests_common/fixtures_static/configs/non_opt_config_tests.json",
                {
                    "POLYAXON_AMQP_URL": "foo",
                    "POLYAXON_BROKER_BACKEND": "rabbitmq",
                    "POLYAXON_RABBITMQ_PASSWORD": "",
                    "POLYAXON_RABBITMQ_USER": "user",
                },
            ]
        )
        config = PlatformConfig.from_dict(config.data)
        assert config.get_broker_url() == "amqp://foo"

        config = ConfigReader.read_configs(
            [
                os.environ,
                "./tests/tests_common/fixtures_static/configs/non_opt_config_tests.json",
                {
                    "POLYAXON_AMQP_URL": "foo",
                    "POLYAXON_BROKER_BACKEND": "rabbitmq",
                    "POLYAXON_RABBITMQ_USER": "",
                    "POLYAXON_RABBITMQ_PASSWORD": "pwd",
                },
            ]
        )
        config = PlatformConfig.from_dict(config.data)
        assert config.get_broker_url() == "amqp://foo"

        config = ConfigReader.read_configs(
            [
                os.environ,
                "./tests/tests_common/fixtures_static/configs/non_opt_config_tests.json",
                {
                    "POLYAXON_AMQP_URL": "foo",
                    "POLYAXON_BROKER_BACKEND": "rabbitmq",
                    "POLYAXON_RABBITMQ_USER": "user",
                    "POLYAXON_RABBITMQ_PASSWORD": "pwd",
                },
            ]
        )
        config = PlatformConfig.from_dict(config.data)
        assert config.get_broker_url() == "amqp://user:pwd@foo"
