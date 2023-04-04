#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from django.core.management import BaseCommand


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--app",
            dest="app",
            default="coredb",
        )

    @staticmethod
    def update_migrations(cursor, app):
        query = "UPDATE django_migrations SET app = 'db' where app='{}'".format(app)
        cursor.execute(query)

    @staticmethod
    def update_table(cursor):
        check_query = (
            "select * from information_schema.tables where table_name='{}'".format(
                "auth_user"
            )
        )
        cursor.execute(check_query)
        if bool(cursor.fetchall()):
            alter_query = "ALTER TABLE auth_user RENAME TO db_user"
            cursor.execute(alter_query)

    def handle(self, *args, **options):
        from django.conf import settings
        from django.db import connection

        if settings.DB_ENGINE_NAME == "sqlite":
            return

        with connection.cursor() as cursor:
            self.update_migrations(cursor, options["app"])
