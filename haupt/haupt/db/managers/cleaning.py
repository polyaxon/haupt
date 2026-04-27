from datetime import timezone as _timezone
from typing import Optional

from clipped.utils.tz import get_datetime_from_now

from django.db.models import Max
from django.db.models.functions import TruncDay, TruncHour


def compact_owner_stats(
    stats_model,
    obj_fk: str,
    obj_id: int,
    pinned_id: Optional[int],
    raw_retention_days: int = 90,
    hourly_retention_days: int = 365,
):
    """Downsample a single owner's stats snapshots in two passes (hourly, daily).

    Tiered retention:
      - up to raw_retention_days: keep every snapshot
      - raw_retention_days .. hourly_retention_days: keep one per hour
      - beyond hourly_retention_days: keep one per day
    Within each bucket we keep the row with the largest id (latest snapshot).
    """
    raw_cutoff = get_datetime_from_now(days=raw_retention_days)
    hourly_cutoff = get_datetime_from_now(days=hourly_retention_days)
    base = stats_model.objects.filter(**{obj_fk: obj_id})

    for trunc_cls, lower, upper in (
        (TruncHour, hourly_cutoff, raw_cutoff),
        (TruncDay, None, hourly_cutoff),
    ):
        qs = base.filter(created_at__lt=upper)
        if lower is not None:
            qs = qs.filter(created_at__gte=lower)
        # Bucket in UTC so downsampling is deterministic regardless of the
        # deployment's configured timezone.
        keep = (
            qs.annotate(_bucket=trunc_cls("created_at", tzinfo=_timezone.utc))
            .values("_bucket")
            .annotate(_keep=Max("id"))
            .values("_keep")
        )
        to_delete = qs.exclude(id__in=keep)
        if pinned_id is not None:
            to_delete = to_delete.exclude(id=pinned_id)
        to_delete.delete()
