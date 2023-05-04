#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from typing import Optional

from haupt.orchestration.scheduler import converter
from polyaxon.k8s.executor.executor import Executor


def start(
    content: str,
    owner_name: str,
    project_name: str,
    run_name: str,
    run_kind: str,
    run_uuid: str,
    namespace: str,
    in_cluster: Optional[bool] = None,
    default_auth: bool = False,
):
    resource = converter.convert(
        owner_name=owner_name,
        project_name=project_name,
        run_name=run_name,
        run_uuid=run_uuid,
        content=content,
        default_auth=default_auth,
    )
    Executor(namespace=namespace, in_cluster=in_cluster).create(
        run_uuid=run_uuid, run_kind=run_kind, resource=resource
    )


def apply(
    content: str,
    owner_name: str,
    project_name: str,
    run_name: str,
    run_kind: str,
    run_uuid: str,
    namespace: str,
    in_cluster: Optional[bool] = None,
    default_auth: bool = False,
):
    resource = converter.convert(
        owner_name=owner_name,
        project_name=project_name,
        run_name=run_name,
        run_uuid=run_uuid,
        content=content,
        default_auth=default_auth,
    )
    Executor(namespace=namespace, in_cluster=in_cluster).apply(
        run_uuid=run_uuid, run_kind=run_kind, resource=resource
    )


def stop(
    run_kind: str, run_uuid: str, namespace: str, in_cluster: Optional[bool] = None
):
    Executor(namespace=namespace, in_cluster=in_cluster).stop(
        run_uuid=run_uuid, run_kind=run_kind
    )


def clean(
    run_kind: str, run_uuid: str, namespace: str, in_cluster: Optional[bool] = None
):
    Executor(namespace=namespace, in_cluster=in_cluster).clean(
        run_uuid=run_uuid, run_kind=run_kind
    )


def make_and_create(
    content: str,
    owner_name: str,
    project_name: str,
    run_name: str,
    run_kind: str,
    run_uuid: str,
    namespace: str,
    in_cluster: Optional[bool] = None,
):
    resource = converter.make_and_convert(
        owner_name=owner_name,
        project_name=project_name,
        run_name=run_name,
        run_uuid=run_uuid,
        content=content,
    )

    Executor(namespace=namespace, in_cluster=in_cluster).create(
        run_uuid=run_uuid, run_kind=run_kind, resource=resource
    )
