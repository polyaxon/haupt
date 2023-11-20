from django.core.management import BaseCommand


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--dbapp",
            dest="dbapp",
            default="coredb",
        )

    @staticmethod
    def _check_table(cursor, table_name):
        check_query = (
            "select * from information_schema.tables where table_name='{}'".format(
                table_name
            )
        )
        cursor.execute(check_query)
        return bool(cursor.fetchall())

    @classmethod
    def update_migrations(cls, cursor, app):
        if cls._check_table(cursor, "django_migrations"):
            query = "UPDATE django_migrations SET app = 'db' where app='{}'".format(app)
            cursor.execute(query)

    @classmethod
    def update_table(cls, cursor):
        if cls._check_table(cursor, "auth_user"):
            alter_query = "ALTER TABLE auth_user RENAME TO db_user"
            cursor.execute(alter_query)

    def handle(self, *args, **options):
        from django.conf import settings
        from django.db import connection

        if settings.DB_ENGINE_NAME == "sqlite":
            return

        with connection.cursor() as cursor:
            self.update_migrations(cursor, options["dbapp"])
