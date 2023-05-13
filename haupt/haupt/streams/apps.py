# isort: skip_file

from django.apps import AppConfig


class StreamsConfig(AppConfig):
    name = "haupt.streams"
    verbose_name = "Streams"

    def ready(self):
        from haupt.common import conf

        conf.validate_and_setup()

        import haupt.common.options.conf_subscriptions  # noqa
