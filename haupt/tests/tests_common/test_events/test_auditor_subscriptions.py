from unittest import TestCase

from haupt.common import auditor
from haupt.common.events.registry import run


class TestEventsSubscriptions(TestCase):
    def setUp(self):
        super().setUp()
        auditor.validate_and_setup()
        # load subscriptions
        from haupt.common.events import auditor_subscriptions  # noqa

    def _assert_events_subscription(self, events):
        for event in events:
            assert auditor.event_manager.knows(event)

    def test_events_subjects_runs(self):
        self._assert_events_subscription(run.EVENTS)
