from typing import Dict, Optional

from haupt.schemas.platform_config import PlatformConfig


def set_celery(
    context, config: PlatformConfig, routes: Dict, schedules: Optional[Dict] = None
):
    context["CELERY_TASK_TRACK_STARTED"] = config.celery_task_track_started
    context["CELERY_BROKER_POOL_LIMIT"] = config.celery_broker_pool_limit
    context["CELERY_BROKER_BACKEND"] = config.broker_backend
    confirm_publish = config.celery_confirm_publish
    context["CELERY_CONFIRM_PUBLISH"] = confirm_publish
    if config.is_rabbitmq_broker and confirm_publish:
        # see https://github.com/celery/celery/issues/5410 for details
        context["CELERY_BROKER_TRANSPORT_OPTIONS"] = {"confirm_publish": True}

    context["CELERY_BROKER_URL"] = config.get_broker_url()

    context["INTERNAL_EXCHANGE"] = config.internal_exchange

    result_bucked = config.celery_result_backend
    if result_bucked:
        context["CELERY_RESULT_BACKEND"] = config.get_redis_url(
            config.celery_result_backend
        )

    context[
        "CELERY_WORKER_PREFETCH_MULTIPLIER"
    ] = config.celery_worker_prefetch_multiplier  # fmt: skip

    context["CELERY_TASK_ALWAYS_EAGER"] = config.celery_task_always_eager
    if config.celery_task_always_eager:
        context["CELERY_BROKER_TRANSPORT"] = "memory"

    context["CELERY_ACCEPT_CONTENT"] = ["application/json"]
    context["CELERY_TASK_DEFAULT_PRIORITY"] = 10
    context["CELERY_TASK_SERIALIZER"] = "json"
    context["CELERY_RESULT_SERIALIZER"] = "json"
    context["CELERY_TASK_IGNORE_RESULT"] = True
    context["CELERY_TIMEZONE"] = config.timezone
    context["CELERY_HARD_TIME_LIMIT_DELAY"] = config.celery_hard_time_limit_delay
    context[
        "CELERY_WORKER_MAX_TASKS_PER_CHILD"
    ] = config.celery_worker_max_tasks_per_child  # fmt: skip
    context[
        "CELERY_WORKER_MAX_MEMORY_PER_CHILD"
    ] = config.celery_worker_max_memory_per_child  # fmt: skip
    context["CELERY_TASK_ROUTES"] = routes
    if schedules:
        context["CELERY_BEAT_SCHEDULE"] = schedules

    context[
        "CLEANING_INTERVALS_ACTIVITY_LOGS"
    ] = config.cleaning_intervals_activity_logs  # fmt: skip
    context[
        "CLEANING_INTERVALS_NOTIFICATIONS"
    ] = config.cleaning_intervals_notifications  # fmt: skip
    context["CLEANING_INTERVALS_ARCHIVES"] = config.cleaning_intervals_archives
    context["CLEANING_INTERVALS_DELETION"] = config.cleaning_intervals_deletion
