import asyncio
import pandas as pd
import pytest
from unittest.mock import AsyncMock, Mock

from clipped.utils.json import orjson_dumps
from haupt.streams.controllers import events as events_module


pytestmark = pytest.mark.streams_mark


# `check_cache=False` is the `force=true` path, which removes local files first
@pytest.mark.parametrize("check_cache", [True, False])
def test_package_event_assets_keeps_paths_inside_the_run(monkeypatch, check_cache):
    paths = [
        "assets/a.png",
        "assets/../file",
        "../x",
        "assets/../../x",
        "/etc/passwd",
        123,
        None,
        "",
    ]
    df = pd.DataFrame({"image": [orjson_dumps({"path": p}) for p in paths]})
    download_files = AsyncMock(return_value=[])
    monkeypatch.setattr(
        events_module, "download_file", AsyncMock(return_value="event.plx")
    )
    monkeypatch.setattr(
        events_module,
        "process_operation_event",
        AsyncMock(return_value={"data": Mock(df=df)}),
    )
    monkeypatch.setattr(events_module, "download_files", download_files)

    asyncio.run(
        events_module.get_archived_operation_event_and_assets(
            fs=Mock(),
            store_path="store",
            run_uuid="uuid",
            event_kind="image",
            event_name="image1",
            check_cache=check_cache,
        )
    )

    assert download_files.await_args.kwargs["subpaths"] == [
        "uuid/assets/a.png",
        "uuid/file",
    ]
    assert download_files.await_args.kwargs["check_cache"] is check_cache


def test_package_event_assets_archive_name_is_a_single_file_name(monkeypatch):
    tar_files = AsyncMock(return_value="archive")
    monkeypatch.setattr(
        events_module,
        "get_archived_operation_event_and_assets",
        AsyncMock(return_value=[]),
    )
    monkeypatch.setattr(events_module, "tar_files", tar_files)

    asyncio.run(
        events_module.get_archived_operation_events_and_assets(
            fs=Mock(),
            store_path="store",
            run_uuid="uuid",
            event_kind="image",
            event_names={"train/loss"},
        )
    )

    assert tar_files.await_args.kwargs["filename"] == "uuid.image.train_loss"
