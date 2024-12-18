from unittest import TestCase

from haupt.common.options.registry import core, scheduler


class TestOptions(TestCase):
    def test_options_core(self):
        assert core.Logging.default is None
        assert core.Logging.is_global() is True
        assert core.Logging.is_optional is False
        assert core.Logging.get_key_subject() == "LOGGING"
        assert core.Logging.get_namespace() is None
        assert core.UiAdminEnabled.default is True
        assert core.UiAdminEnabled.is_global() is True
        assert core.UiAdminEnabled.is_optional is True
        assert core.UiAdminEnabled.get_key_subject() == "UI_ADMIN_ENABLED"
        assert core.UiAdminEnabled.get_namespace() is None
        assert core.UiBaseUrl.get_key_subject() == "UI_BASE_URL"
        assert core.UiAssetsVersion.get_key_subject() == "UI_ASSETS_VERSION"
        assert core.UiDefaultStreamsUrl.get_key_subject() == "UI_DEFAULT_STREAMS_URL"
        assert core.UiDefaultStreamsUrl.get_namespace() is None
        assert core.UiSingleUrl.get_key_subject() == "UI_SINGLE_URL"
        assert core.UiSingleUrl.get_namespace() is None

    def test_options_scheduler(self):
        assert scheduler.SchedulerCountdown.get_namespace() is None
        assert (
            scheduler.SchedulerCountdown.get_key_subject()
            == "SCHEDULER_GLOBAL_COUNTDOWN"
        )
