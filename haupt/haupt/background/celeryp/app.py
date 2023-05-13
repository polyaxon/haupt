from celery import Celery, states

from django.apps import apps

STATES = states

app = Celery("haupt")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(lambda: [n.name for n in apps.get_app_configs()])
