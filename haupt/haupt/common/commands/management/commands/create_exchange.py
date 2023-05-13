from django.core.management import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        from haupt.common import workers
        from kombu import Exchange

        Exchange(
            "internal", type="topic", channel=workers.app.connection().channel()
        ).declare()
