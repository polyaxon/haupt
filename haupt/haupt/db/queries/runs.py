from haupt.db.abstracts.getter import get_run_model

STATUS_UPDATE_COLUMNS_ONLY = [
    "id",
    "status",
    "status_conditions",
    "started_at",
    "updated_at",
    "finished_at",
    "duration",
    "wait_time",
    "meta_info",
]
STATUS_UPDATE_COLUMNS_DEFER = [
    "original",
    "cloning_kind",
    "description",
    "inputs",
    "outputs",
    "tags",
    "description",
    "live_state",
    "readme",
    "content",
    "is_managed",
    "pending",
]
DEFAULT_COLUMNS_DEFER = ["description", "readme", "content", "raw_content"]

run_model = get_run_model()

runs = run_model.objects
