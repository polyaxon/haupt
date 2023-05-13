from polyaxon.k8s.manager.async_manager import AsyncK8sManager


async def get_pods(
    k8s_manager: AsyncK8sManager,
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
