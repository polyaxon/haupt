from unittest import TestCase

from haupt.common import conf
from haupt.common.options.registry import (
    cleaning,
    containers,
    core,
    installation,
    k8s,
    scheduler,
    stats,
)


class TestConfSubscriptions(TestCase):
    def setUp(self):
        super().setUp()
        conf.validate_and_setup()
        # load subscriptions
        import haupt.common.options.conf_subscriptions  # noqa

    def _assert_options_subscriptions(self, options):
        for option in options:
            assert conf.option_manager.knows(option)

    def test_core_subscriptions(self):
        self._assert_options_subscriptions(core.OPTIONS)

    def test_installation_subscriptions(self):
        self._assert_options_subscriptions(installation.OPTIONS)

    def test_k8s_subscriptions(self):
        self._assert_options_subscriptions(k8s.OPTIONS)

    def test_scheduler_subscriptions(self):
        self._assert_options_subscriptions(scheduler.OPTIONS)

    def test_containers_subscriptions(self):
        self._assert_options_subscriptions(containers.OPTIONS)

    def test_stats_subscriptions(self):
        self._assert_options_subscriptions(stats.OPTIONS)

    def test_cleaning_subscriptions(self):
        self._assert_options_subscriptions(cleaning.OPTIONS)
