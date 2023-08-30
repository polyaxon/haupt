# isort: skip_file

from django.apps import AppConfig


class APIsConfig(AppConfig):
    name = "haupt.apis"
    verbose_name = "APIs"

    def ready(self):
        from haupt.common import conf
        from haupt.common import auditor
        from haupt.orchestration import executor, operations
        from haupt.common import query

        conf.validate_and_setup()
        query.validate_and_setup()
        operations.validate_and_setup()
        executor.validate_and_setup()
        auditor.validate_and_setup()

        import haupt.db.signals.runs  # noqa
        import haupt.db.signals.versions  # noqa
        import haupt.db.signals.bookmarks  # noqa
        import haupt.db.signals.stats  # noqa

        import haupt.common.options.conf_subscriptions  # noqa
        from haupt.common.events import auditor_subscriptions  # noqa
        from haupt.db.administration import register  # noqa
