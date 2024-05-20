from typing import List, Optional
from typing_extensions import Literal

from clipped.compact.pydantic import Extra, Field, validator
from clipped.utils.logging import DEFAULT_LOGS_ROOT

from polyaxon._contexts import paths as ctx_paths
from polyaxon._env_vars.keys import (
    ENV_KEYS_ARCHIVES_ROOT,
    ENV_KEYS_DNS_BACKEND,
    ENV_KEYS_DNS_CUSTOM_CLUSTER,
    ENV_KEYS_DNS_PREFIX,
    ENV_KEYS_DNS_USE_RESOLVER,
    ENV_KEYS_K8S_NAMESPACE,
    ENV_KEYS_LOG_LEVEL,
    ENV_KEYS_LOGS_ROOT,
    ENV_KEYS_NGINX_INDENT_CHAR,
    ENV_KEYS_NGINX_INDENT_WIDTH,
    ENV_KEYS_NGINX_TIMEOUT,
    ENV_KEYS_PROXY_API_HOST,
    ENV_KEYS_PROXY_API_PORT,
    ENV_KEYS_PROXY_API_TARGET_PORT,
    ENV_KEYS_PROXY_API_USE_RESOLVER,
    ENV_KEYS_PROXY_AUTH_ENABLED,
    ENV_KEYS_PROXY_AUTH_EXTERNAL,
    ENV_KEYS_PROXY_AUTH_USE_RESOLVER,
    ENV_KEYS_PROXY_FORWARD_PROXY_HOST,
    ENV_KEYS_PROXY_FORWARD_PROXY_KIND,
    ENV_KEYS_PROXY_FORWARD_PROXY_PORT,
    ENV_KEYS_PROXY_FORWARD_PROXY_PROTOCOL,
    ENV_KEYS_PROXY_GATEWAY_HOST,
    ENV_KEYS_PROXY_GATEWAY_PORT,
    ENV_KEYS_PROXY_GATEWAY_TARGET_PORT,
    ENV_KEYS_PROXY_HAS_FORWARD_PROXY,
    ENV_KEYS_PROXY_NAMESPACES,
    ENV_KEYS_PROXY_SSL_ENABLED,
    ENV_KEYS_PROXY_SSL_PATH,
    ENV_KEYS_PROXY_STREAMS_HOST,
    ENV_KEYS_PROXY_STREAMS_PORT,
    ENV_KEYS_PROXY_STREAMS_TARGET_PORT,
    ENV_KEYS_STATIC_ROOT,
    ENV_KEYS_STATIC_URL,
    ENV_KEYS_UI_ADMIN_ENABLED,
)
from polyaxon._schemas.base import BaseSchemaModel
from polyaxon.api import STATIC_V1


class ProxiesConfig(BaseSchemaModel):
    _IDENTIFIER = "proxies"
    _DEFAULT_TARGET_PORT = 8000
    _DEFAULT_PORT = 80

    namespace: Optional[str] = Field(alias=ENV_KEYS_K8S_NAMESPACE)
    namespaces: Optional[List[str]] = Field(alias=ENV_KEYS_PROXY_NAMESPACES)
    gateway_port: Optional[int] = Field(
        alias=ENV_KEYS_PROXY_GATEWAY_PORT, default=_DEFAULT_PORT
    )
    gateway_target_port: Optional[int] = Field(
        alias=ENV_KEYS_PROXY_GATEWAY_TARGET_PORT, default=_DEFAULT_TARGET_PORT
    )
    gateway_host: Optional[str] = Field(
        alias=ENV_KEYS_PROXY_GATEWAY_HOST, default="polyaxon-polyaxon-gateway"
    )
    streams_port: Optional[int] = Field(
        alias=ENV_KEYS_PROXY_STREAMS_PORT, default=_DEFAULT_PORT
    )
    streams_target_port: Optional[int] = Field(
        alias=ENV_KEYS_PROXY_STREAMS_TARGET_PORT, default=_DEFAULT_TARGET_PORT
    )
    streams_host: Optional[str] = Field(
        alias=ENV_KEYS_PROXY_STREAMS_HOST, default="polyaxon-polyaxon-streams"
    )
    api_port: Optional[int] = Field(
        alias=ENV_KEYS_PROXY_API_PORT, default=_DEFAULT_PORT
    )
    api_target_port: Optional[int] = Field(
        alias=ENV_KEYS_PROXY_API_TARGET_PORT, default=_DEFAULT_TARGET_PORT
    )
    api_host: Optional[str] = Field(
        alias=ENV_KEYS_PROXY_API_HOST, default="polyaxon-polyaxon-api"
    )
    api_use_resolver: Optional[bool] = Field(
        alias=ENV_KEYS_PROXY_API_USE_RESOLVER, default=False
    )
    auth_enabled: Optional[bool] = Field(
        alias=ENV_KEYS_PROXY_AUTH_ENABLED, default=False
    )
    auth_external: Optional[str] = Field(alias=ENV_KEYS_PROXY_AUTH_EXTERNAL)
    auth_use_resolver: Optional[bool] = Field(
        alias=ENV_KEYS_PROXY_AUTH_USE_RESOLVER, default=False
    )
    ssl_enabled: Optional[bool] = Field(alias=ENV_KEYS_PROXY_SSL_ENABLED, default=False)
    ssl_path: Optional[str] = Field(
        alias=ENV_KEYS_PROXY_SSL_PATH, default="/etc/ssl/polyaxon"
    )
    dns_use_resolver: Optional[bool] = Field(
        alias=ENV_KEYS_DNS_USE_RESOLVER, default=False
    )
    dns_custom_cluster: Optional[str] = Field(
        alias=ENV_KEYS_DNS_CUSTOM_CLUSTER, default="cluster.local"
    )
    dns_backend: Optional[str] = Field(alias=ENV_KEYS_DNS_BACKEND, default="kube-dns")
    dns_prefix: Optional[str] = Field(alias=ENV_KEYS_DNS_PREFIX)
    logs_root: Optional[str] = Field(
        alias=ENV_KEYS_LOGS_ROOT, default=DEFAULT_LOGS_ROOT
    )
    log_level: Optional[str] = Field(alias=ENV_KEYS_LOG_LEVEL)
    nginx_timeout: Optional[int] = Field(alias=ENV_KEYS_NGINX_TIMEOUT, default=650)
    nginx_indent_char: Optional[str] = Field(
        alias=ENV_KEYS_NGINX_INDENT_CHAR, default=" "
    )
    nginx_indent_width: Optional[int] = Field(
        alias=ENV_KEYS_NGINX_INDENT_WIDTH, default=4
    )
    archives_root: Optional[str] = Field(
        alias=ENV_KEYS_ARCHIVES_ROOT, default=ctx_paths.CONTEXT_ARCHIVES_ROOT
    )
    static_root: Optional[str] = Field(
        alias=ENV_KEYS_STATIC_ROOT, default="/{}".format(STATIC_V1)
    )
    static_url: Optional[str] = Field(alias=ENV_KEYS_STATIC_URL)
    ui_admin_enabled: Optional[bool] = Field(alias=ENV_KEYS_UI_ADMIN_ENABLED)
    has_forward_proxy: Optional[bool] = Field(alias=ENV_KEYS_PROXY_HAS_FORWARD_PROXY)
    forward_proxy_port: Optional[int] = Field(alias=ENV_KEYS_PROXY_FORWARD_PROXY_PORT)
    forward_proxy_host: Optional[str] = Field(alias=ENV_KEYS_PROXY_FORWARD_PROXY_HOST)
    forward_proxy_protocol: Optional[str] = Field(
        alias=ENV_KEYS_PROXY_FORWARD_PROXY_PROTOCOL
    )
    forward_proxy_kind: Optional[Literal["transparent", "connect"]] = Field(
        alias=ENV_KEYS_PROXY_FORWARD_PROXY_KIND
    )

    class Config:
        extra = Extra.ignore

    @validator("log_level", always=True)
    def validate_log_level(cls, v):
        return (v or "warn").lower()
