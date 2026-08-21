from django.core.management import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        from kombu import Exchange

        from haupt.common import workers

        Exchange(
            "internal", type="topic", channel=workers.app.connection().channel()
        ).declare()
