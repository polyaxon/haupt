from django.conf import settings

from haupt.common.auditor.manager import event_manager
from haupt.common.auditor.service import AuditorService
from haupt.common.service_interface import LazyServiceWrapper


def get_auditor_backend_path():
    return settings.AUDITOR_BACKEND or "haupt.common.auditor.service.AuditorService"


def get_auditor_options():
    return {
        "auditor_events_task": settings.AUDITOR_EVENTS_TASK,
        "workers_service": settings.WORKERS_SERVICE,
        "executor_service": settings.EXECUTOR_SERVICE or "haupt.orchestration.executor",
    }


backend = LazyServiceWrapper(
    backend_base=AuditorService,
    backend_path=get_auditor_backend_path(),
    options=get_auditor_options(),
)
backend.expose(locals())

subscribe = event_manager.subscribe
