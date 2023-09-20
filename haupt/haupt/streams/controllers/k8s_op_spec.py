from polyaxon._k8s.manager.async_manager import AsyncK8sManager
from polyaxon.schemas import V1RunKind


async def get_op_spec(
    k8s_manager: AsyncK8sManager,
    run_uuid: str,
    run_kind: str,
):
    pods = await k8s_manager.list_pods(
        label_selector=k8s_manager.get_managed_by_polyaxon(run_uuid)
    )
    pods_list = {}
    for pod in pods or []:
        pods_list[
            pod.metadata.name
        ] = k8s_manager.api_client.sanitize_for_serialization(pod)
    data = {"pods": pods_list}
    if V1RunKind.has_service(run_kind):
        services = await k8s_manager.list_services(
            label_selector=k8s_manager.get_managed_by_polyaxon(run_uuid)
        )
        services_list = {}
        for service in services or []:
            services_list[
                service.metadata.name
            ] = k8s_manager.api_client.sanitize_for_serialization(service)
        data["services"] = services_list
    return data
