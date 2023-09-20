import logging

from typing import List

from polyaxon import settings
from polyaxon._k8s import converter
from polyaxon._k8s.executor.async_executor import AsyncExecutor
from polyaxon._operations import get_notifier_operation
from polyaxon._polyaxonfile import OperationSpecification
from polyaxon.schemas import V1StatusCondition

logger = logging.getLogger("haupt.streams.notification")


async def notify_run(
    namespace: str,
    owner: str,
    project: str,
    run_uuid: str,
    run_name: str,
    condition: V1StatusCondition,
    connections: List[str],
):
    executor = AsyncExecutor(namespace=namespace)
    await executor.refresh()
    for connection in connections:
        connection_type = settings.AGENT_CONFIG.connections_by_names.get(connection)
        if not connection_type:
            logger.warning(
                "Could not create notification using connection {}, "
                "the connection was not found or not set correctly.".format(
                    connection_type
                )
            )
            continue

        operation = get_notifier_operation(
            connection=connection,
            backend=connection_type.kind,
            owner=owner,
            project=project,
            run_uuid=run_uuid,
            run_name=run_name,
            condition=condition.to_dict(),
        )
        compiled_operation = OperationSpecification.compile_operation(operation)
        resource = converter.make(
            owner_name=owner,
            project_name=project,
            project_uuid=project,
            run_uuid=run_uuid,
            run_name=run_name,
            run_path=run_uuid,
            compiled_operation=compiled_operation,
            params=operation.params,
        )
        await executor.create(
            run_uuid=run_uuid,
            run_kind=compiled_operation.get_run_kind(),
            resource=resource,
        )
