from django.apps import AppConfig


class DBConfig(AppConfig):
    default_auto_field = "django.db.models.AutoField"
    name = "haupt.db.sqlite.db"
    verbose_name = "DB"
