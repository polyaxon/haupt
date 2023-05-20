from django.conf import settings

from haupt.common.service_interface import LazyServiceWrapper
from haupt.orchestration.executor.manager import event_manager
from haupt.orchestration.executor.service import ExecutorService


def get_executor_backend_path():
    return settings.EXECUTOR_BACKEND


def get_executor_options():
    return {
        "workers_service": settings.WORKERS_SERVICE,
        "handlers_service": settings.HANDLERS_SERVICE,
    }


backend = LazyServiceWrapper(
    backend_base=ExecutorService,
    backend_path=settings.EXECUTOR_BACKEND,
    options=get_executor_options(),
)
backend.expose(locals())

subscribe = event_manager.subscribe
