#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

import os

from pathlib import Path
from typing import List

from haupt import pkg
from polyaxon.config.manager import ConfigManager as BaseConfigManager
from polyaxon.env_vars.keys import (
    EV_KEYS_DEBUG,
    EV_KEYS_ENVIRONMENT,
    EV_KEYS_LOG_LEVEL,
    EV_KEYS_PLATFORM_CONFIG,
    EV_KEYS_SERVICE,
    EV_KEYS_TIME_ZONE,
)
from polyaxon.k8s.namespace import DEFAULT_NAMESPACE


class ConfigManager(BaseConfigManager):
    def __init__(self, **params):
        super().__init__(**params)
        self._env = self.get(
            EV_KEYS_ENVIRONMENT, "str", is_optional=True, default="local"
        )
        self._config_module = self.get(
            "POLYAXON_CONFIG_MODULE", "str", is_optional=True, default="polyconf"
        )
        self._root_dir = self.get_value("POLYAXON_CONFIG_ROOT_DIR")
        self._service = self.get(
            EV_KEYS_SERVICE, "str", is_local=True, is_optional=True
        )
        self._is_debug_mode = self.get(
            EV_KEYS_DEBUG, "bool", is_optional=True, default=False
        )
        self._db_engine_name = self.get(
            "POLYAXON_DB_ENGINE", "str", default="sqlite", is_optional=True
        )
        self._namespace = self.get(
            "POLYAXON_K8S_NAMESPACE",
            "str",
            is_optional=True,
            default=DEFAULT_NAMESPACE,
        )
        self._log_level = self.get(
            EV_KEYS_LOG_LEVEL,
            "str",
            is_local=True,
            is_optional=True,
            default="WARNING",
        ).upper()
        self._timezone = self.get(
            EV_KEYS_TIME_ZONE, "str", is_optional=True, default="UTC"
        )
        self._scheduler_enabled = self.get(
            "POLYAXON_SCHEDULER_ENABLED", "bool", is_optional=True, default=False
        )
        self._chart_version = self.get(
            "POLYAXON_CHART_VERSION", "str", is_optional=True, default=pkg.VERSION
        )
        self._redis_protocol = self.get(
            "POLYAXON_REDIS_PROTOCOL", "str", is_optional=True, default="redis"
        )
        self._broker_backend = self.get(
            "POLYAXON_BROKER_BACKEND",
            "str",
            is_optional=True,
            options=["redis", "rabbitmq"],
        )
        self._redis_password = self.get(
            "POLYAXON_REDIS_PASSWORD",
            "str",
            is_optional=True,
            is_secret=True,
            is_local=True,
        )

    @property
    def namespace(self) -> str:
        return self._namespace

    @property
    def config_module(self) -> str:
        return self._config_module

    @property
    def root_dir(self) -> Path:
        return self._root_dir

    @property
    def db_engine_name(self) -> str:
        return self._db_engine_name

    @property
    def is_sqlite_db_engine(self) -> bool:
        return self._db_engine_name == "sqlite"

    @property
    def is_pgsql_db_engine(self) -> bool:
        return self._db_engine_name == "pgsql"

    @property
    def chart_version(self) -> str:
        return self._chart_version

    @property
    def service(self) -> str:
        return self._service

    @property
    def is_streams_service(self) -> bool:
        return self.service == "streams"

    @property
    def is_monolith_service(self) -> bool:
        return self.service == "monolith"

    @property
    def is_api_service(self) -> bool:
        return self.service == "api" or self.is_monolith_service

    @property
    def is_scheduler_service(self) -> bool:
        return self.service == "scheduler" or self.is_monolith_service

    @property
    def is_debug_mode(self) -> bool:
        return self._is_debug_mode

    @property
    def env(self) -> str:
        return self._env

    @property
    def is_test_env(self) -> bool:
        return self.env == "test"

    @property
    def is_local_env(self) -> bool:
        if self.env == "local":
            return True
        return False

    @property
    def is_staging_env(self) -> bool:
        if self.env == "staging":
            return True
        return False

    @property
    def is_production_env(self) -> bool:
        if self.env == "production":
            return True
        return False

    @property
    def log_handlers(self) -> List[str]:
        return ["console"]

    @property
    def log_level(self) -> str:
        if self.is_staging_env or self.is_local_env or self.is_test_env:
            return self._log_level
        if self._log_level == "DEBUG":
            return "INFO"
        return self._log_level

    @property
    def timezone(self) -> str:
        return self._timezone

    @property
    def scheduler_enabled(self) -> bool:
        return self._scheduler_enabled

    @property
    def broker_backend(self) -> str:
        return self._broker_backend

    @property
    def is_redis_broker(self):
        return self.broker_backend == "redis"

    @property
    def is_rabbitmq_broker(self):
        return self.broker_backend == "rabbitmq"

    def get_redis_url(self, env_url_name) -> str:
        redis_url = self.get(env_url_name, "str")
        if self._redis_password:
            redis_url = ":{}@{}".format(self._redis_password, redis_url)
        return "{}://{}".format(self._redis_protocol, redis_url)

    def _get_rabbitmq_broker_url(self) -> str:
        amqp_url = self.get("POLYAXON_AMQP_URL", "str")
        rabbitmq_user = self.get("POLYAXON_RABBITMQ_USER", "str", is_optional=True)
        rabbitmq_password = self.get(
            "POLYAXON_RABBITMQ_PASSWORD",
            "str",
            is_secret=True,
            is_local=True,
            is_optional=True,
        )
        if rabbitmq_user and rabbitmq_password:
            return "amqp://{user}:{password}@{url}".format(
                user=rabbitmq_user, password=rabbitmq_password, url=amqp_url
            )

        return "amqp://{url}".format(url=amqp_url)

    def get_broker_url(self) -> str:
        if self.is_redis_broker:
            return self.get_redis_url("POLYAXON_REDIS_CELERY_BROKER_URL")
        if self.is_rabbitmq_broker:
            return self._get_rabbitmq_broker_url()


def get_config(file_path):
    def base_directory():
        root = Path(os.path.abspath(file_path))
        root.resolve()
        return root.parent.parent

    root_dir = base_directory()

    config_module = "polyconf"
    config_prefix = os.environ.get("CONFIG_PREFIX")
    if config_prefix:
        config_module = "{}.{}".format(config_prefix, config_module)
    config_values = [
        os.environ,
        {"POLYAXON_CONFIG_MODULE": config_module, "POLYAXON_CONFIG_ROOT_DIR": root_dir},
    ]

    platform_config = os.getenv(EV_KEYS_PLATFORM_CONFIG)
    if platform_config and os.path.isfile(platform_config):
        config_values.append(platform_config)

    return ConfigManager.read_configs(config_values)
