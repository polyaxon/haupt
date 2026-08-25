import os
from unittest import TestCase

from clipped.compact.pydantic import ValidationError
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

    def test_get_broker_url(self):
        os.environ["POLYAXON_ENVIRONMENT"] = "testing"
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

    def test_get_invalid_broker_url(self):
        rabbitmq_configs = [
            {
                "POLYAXON_AMQP_URL": "foo",
                "POLYAXON_BROKER_BACKEND": "rabbitmq",
                "POLYAXON_REDIS_CELERY_BROKER_URL": "foo",
            },
            {
                "POLYAXON_AMQP_URL": "foo",
                "POLYAXON_BROKER_BACKEND": "rabbitmq",
                "POLYAXON_RABBITMQ_PASSWORD": "",
                "POLYAXON_REDIS_CELERY_BROKER_URL": "foo",
            },
            {
                "POLYAXON_AMQP_URL": "foo",
                "POLYAXON_BROKER_BACKEND": "rabbitmq",
                "POLYAXON_RABBITMQ_PASSWORD": "",
                "POLYAXON_RABBITMQ_USER": "user",
            },
            {
                "POLYAXON_AMQP_URL": "foo",
                "POLYAXON_BROKER_BACKEND": "rabbitmq",
                "POLYAXON_RABBITMQ_USER": "",
                "POLYAXON_RABBITMQ_PASSWORD": "pwd",
            },
            {
                "POLYAXON_AMQP_URL": "foo",
                "POLYAXON_BROKER_BACKEND": "rabbitmq",
                "POLYAXON_RABBITMQ_USER": "user",
                "POLYAXON_RABBITMQ_PASSWORD": "pwd",
            },
        ]

        for rabbitmq_config in rabbitmq_configs:
            with self.subTest(rabbitmq_config=rabbitmq_config):
                config = ConfigReader.read_configs(
                    [
                        os.environ,
                        "./tests/tests_common/fixtures_static/configs/non_opt_config_tests.json",
                        rabbitmq_config,
                    ]
                )
                with self.assertRaises(ValidationError):
                    PlatformConfig.from_dict(config.data)
