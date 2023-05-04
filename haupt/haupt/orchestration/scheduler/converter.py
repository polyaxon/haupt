#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from typing import Dict, Optional

from polyaxon.compiler.resolver import AgentResolver
from polyaxon.k8s import converter
from polyaxon.polyaxonfile import CompiledOperationSpecification, OperationSpecification
from polyaxon.schemas.cli.agent_config import AgentConfig


def convert(
    owner_name: str,
    project_name: str,
    run_name: str,
    run_uuid: str,
    content: str,
    default_auth: bool,
    agent_content: Optional[str] = None,
) -> Dict:
    # TODO: Refactor and use agent `._convert`
    agent_env = AgentResolver.construct()
    compiled_operation = CompiledOperationSpecification.read(content)

    agent_env.resolve(
        compiled_operation=compiled_operation,
        agent_config=AgentConfig.read(agent_content) if agent_content else None,
    )
    return converter.convert(
        compiled_operation=compiled_operation,
        owner_name=owner_name,
        project_name=project_name,
        run_name=run_name,
        run_uuid=run_uuid,
        namespace=agent_env.namespace,
        polyaxon_init=agent_env.polyaxon_init,
        polyaxon_sidecar=agent_env.polyaxon_sidecar,
        run_path=run_uuid,
        artifacts_store=agent_env.artifacts_store,
        connection_by_names=agent_env.connection_by_names,
        secrets=agent_env.secrets,
        config_maps=agent_env.config_maps,
        default_sa=agent_env.default_sa,
        default_auth=default_auth,
    )


def make_and_convert(
    owner_name: str,
    project_name: str,
    run_uuid: str,
    run_name: str,
    content: str,
    default_auth: bool = False,
):
    # TODO: Refactor and use agent `._make_and_convert`
    operation = OperationSpecification.read(content)
    compiled_operation = OperationSpecification.compile_operation(operation)
    return converter.make(
        owner_name=owner_name,
        project_name=project_name,
        project_uuid=project_name,
        run_uuid=run_uuid,
        run_name=run_name,
        run_path=run_uuid,
        compiled_operation=compiled_operation,
        params=operation.params,
        default_auth=default_auth,
    )
