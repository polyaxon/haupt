import logging

from typing import Optional

from clipped.compact.pydantic import Field, StrictInt, StrictStr, root_validator
from clipped.utils.http import clean_host
from clipped.utils.paths import check_or_create_path

from polyaxon._env_vars.keys import (
    ENV_KEYS_K8S_NAMESPACE,
    ENV_KEYS_SANDBOX_DEBUG,
    ENV_KEYS_SANDBOX_HOST,
    ENV_KEYS_SANDBOX_IS_LOCAL,
    ENV_KEYS_SANDBOX_PER_CORE,
    ENV_KEYS_SANDBOX_PORT,
    ENV_KEYS_SANDBOX_ROOT,
    ENV_KEYS_SANDBOX_SSL_ENABLED,
    ENV_KEYS_SANDBOX_WORKERS,
)
from polyaxon._schemas.agent import AgentConfig

_logger = logging.getLogger("sandbox.config")


class SandboxConfig(AgentConfig):
    _IDENTIFIER = "sandbox"

    namespace: Optional[StrictStr] = Field(
        alias=ENV_KEYS_K8S_NAMESPACE, default="sandbox"
    )
    port: Optional[StrictInt] = Field(alias=ENV_KEYS_SANDBOX_PORT)
    host: Optional[StrictStr] = Field(alias=ENV_KEYS_SANDBOX_HOST)
    ssl_enabled: Optional[bool] = Field(alias=ENV_KEYS_SANDBOX_SSL_ENABLED)
    debug: Optional[bool] = Field(alias=ENV_KEYS_SANDBOX_DEBUG)
    workers: Optional[StrictInt] = Field(alias=ENV_KEYS_SANDBOX_WORKERS)
    per_core: Optional[bool] = Field(alias=ENV_KEYS_SANDBOX_PER_CORE)
    is_local: Optional[bool] = Field(alias=ENV_KEYS_SANDBOX_IS_LOCAL)
    path: Optional[StrictStr] = Field(alias=ENV_KEYS_SANDBOX_ROOT)

    def __init__(
        self,
        host: Optional[str] = None,
        **data,
    ):
        super().__init__(
            host=clean_host(host) if host else host,
            **data,
        )

    @root_validator(pre=True)
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
        if (
            not values.get("is_local")
            and not values.get(ENV_KEYS_SANDBOX_IS_LOCAL)
            and "isLocal" in values
        ):
            values[ENV_KEYS_SANDBOX_IS_LOCAL] = values["isLocal"]
        return values

    def mount_sandbox(self, path: Optional[str] = None):
        from polyaxon._contexts.paths import mount_sandbox

        self.path = mount_sandbox(path=self.path or path)
        try:
            check_or_create_path(self.path, is_dir=True)
        except Exception as e:
            _logger.error("Could not create sandbox path `%s`.", self.path)
            raise e
