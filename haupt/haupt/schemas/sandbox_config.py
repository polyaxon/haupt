import logging

from typing import Optional

from clipped.compact.pydantic import (
    Field,
    StrictInt,
    StrictStr,
    model_validator,
    validation_before,
)
from clipped.utils.http import clean_host
from clipped.utils.paths import check_or_create_path

from polyaxon._env_vars.keys import (
    ENV_KEYS_K8S_NAMESPACE,
    ENV_KEYS_SANDBOX_DEBUG,
    ENV_KEYS_SANDBOX_HOST,
    ENV_KEYS_SANDBOX_PER_CORE,
    ENV_KEYS_SANDBOX_PORT,
    ENV_KEYS_SANDBOX_SSL_ENABLED,
    ENV_KEYS_SANDBOX_WORKERS,
    ENV_KEYS_SERVICE_MODE,
)
from polyaxon._schemas.agent import AgentConfig
from polyaxon._services import PolyaxonServices

_logger = logging.getLogger("sandbox.config")


class SandboxConfig(AgentConfig):
    _IDENTIFIER = "sandbox"

    namespace: Optional[StrictStr] = Field(
        alias=ENV_KEYS_K8S_NAMESPACE, default="sandbox"
    )
    port: Optional[StrictInt] = Field(alias=ENV_KEYS_SANDBOX_PORT, default=None)
    host: Optional[StrictStr] = Field(alias=ENV_KEYS_SANDBOX_HOST, default=None)
    ssl_enabled: Optional[bool] = Field(
        alias=ENV_KEYS_SANDBOX_SSL_ENABLED, default=None
    )
    debug: Optional[bool] = Field(alias=ENV_KEYS_SANDBOX_DEBUG, default=None)
    workers: Optional[StrictInt] = Field(alias=ENV_KEYS_SANDBOX_WORKERS, default=None)
    per_core: Optional[bool] = Field(alias=ENV_KEYS_SANDBOX_PER_CORE, default=None)
    mode: Optional[StrictStr] = Field(alias=ENV_KEYS_SERVICE_MODE, default=None)

    def __init__(
        self,
        host: Optional[str] = None,
        **data,
    ):
        super().__init__(
            host=clean_host(host) if host else host,
            **data,
        )

    @model_validator(**validation_before)
    def handle_camel_case_sandbox(cls, values):
        if (
            not values.get("ssl_enabled")
            and not values.get(ENV_KEYS_SANDBOX_SSL_ENABLED)
            and "sslEnabled" in values
        ):
            values[ENV_KEYS_SANDBOX_SSL_ENABLED] = values["sslEnabled"]
        if (
            not values.get("per_core")
            and not values.get(ENV_KEYS_SANDBOX_PER_CORE)
            and "perCore" in values
        ):
            values[ENV_KEYS_SANDBOX_PER_CORE] = values["perCore"]
        return values

    def mount_sandbox(self, path: Optional[str] = None):
        from polyaxon._contexts.paths import mount_sandbox

        if not path:
            return

        mount_sandbox(path=path)
        try:
            check_or_create_path(path, is_dir=True)
        except Exception as e:
            _logger.error("Could not create sandbox path `%s`.", path)
            raise e

    @property
    def is_viewer(self):
        return self.mode == PolyaxonServices.VIEWER
