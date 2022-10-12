#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from marshmallow import fields

from polyaxon.env_vars.keys import (
    EV_KEYS_SANDBOX_DEBUG,
    EV_KEYS_SANDBOX_HOST,
    EV_KEYS_SANDBOX_PER_CORE,
    EV_KEYS_SANDBOX_PORT,
    EV_KEYS_SANDBOX_SSL_ENABLED,
    EV_KEYS_SANDBOX_WORKERS,
)
from polyaxon.schemas.cli.agent_config import BaseAgentConfig, BaseAgentSchema
from polyaxon.utils.http_utils import clean_host


class SandboxSchema(BaseAgentSchema):
    REQUIRED_ARTIFACTS_STORE = False

    port = fields.Int(allow_none=True, data_key=EV_KEYS_SANDBOX_PORT)
    host = fields.Str(allow_none=True, data_key=EV_KEYS_SANDBOX_HOST)
    ssl_enabled = fields.Bool(allow_none=True, data_key=EV_KEYS_SANDBOX_SSL_ENABLED)
    debug = fields.Bool(allow_none=True, data_key=EV_KEYS_SANDBOX_DEBUG)
    workers = fields.Int(allow_none=True, data_key=EV_KEYS_SANDBOX_WORKERS)
    per_core = fields.Bool(allow_none=True, data_key=EV_KEYS_SANDBOX_PER_CORE)

    @staticmethod
    def schema_config():
        return SandboxConfig


class SandboxConfig(BaseAgentConfig):
    SCHEMA = SandboxSchema
    IDENTIFIER = "sandbox"
    REDUCED_ATTRIBUTES = BaseAgentConfig.REDUCED_ATTRIBUTES + [
        EV_KEYS_SANDBOX_PORT,
        EV_KEYS_SANDBOX_HOST,
        EV_KEYS_SANDBOX_SSL_ENABLED,
        EV_KEYS_SANDBOX_DEBUG,
        EV_KEYS_SANDBOX_WORKERS,
        EV_KEYS_SANDBOX_PER_CORE,
    ]

    def __init__(
        self,
        artifacts_store=None,
        connections=None,
        port: int = None,
        host: str = None,
        ssl_enabled: bool = None,
        debug: bool = None,
        workers: int = None,
        per_core: bool = None,
        **kwargs,
    ):
        super().__init__(
            artifacts_store=artifacts_store,
            connections=connections,
            namespace="sandbox",
            **kwargs,
        )
        self.host = clean_host(host) if host else host
        self.port = port
        self.ssl_enabled = ssl_enabled
        self.debug = debug
        self.workers = workers
        self.per_core = per_core
