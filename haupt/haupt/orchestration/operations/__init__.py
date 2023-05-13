from django.conf import settings

from haupt.common.service_interface import LazyServiceWrapper
from haupt.orchestration.operations.service import OperationInitSpec, OperationsService


def get_operation_backend_path():
    return (
        settings.OPERATIONS_BACKEND
        or "haupt.orchestration.operations.service.OperationsService"
    )


backend = LazyServiceWrapper(
    backend_base=OperationsService,
    backend_path=get_operation_backend_path(),
    options={},
)
backend.expose(locals())
