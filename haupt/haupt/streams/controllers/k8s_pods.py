#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
from polyaxon.k8s.async_manager import AsyncK8SManager


async def get_pods(
    k8s_manager: AsyncK8SManager,
    run_uuid: str,
):
    pods = await k8s_manager.list_pods(
        label_selector=k8s_manager.get_managed_by_polyaxon(run_uuid)
    )
    pods_list = {}
    for pod in pods or []:
        pods_list[
            pod.metadata.name
        ] = k8s_manager.api_client.sanitize_for_serialization(pod)
    return pods_list
