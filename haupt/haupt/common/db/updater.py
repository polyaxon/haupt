from clipped.decorators.memoization import memoize

from django.conf import settings
from django.db import connection


class RawBulkUpdater:
    """
    This class does bulk updates and behaves the same way as the RawBulkInserter
    """

    def __init__(self, model, query_fields, value_fields, chunk_size=40000):
        """
        Params:
            model: model class
            query_fields: iterable of query field names to be used for the where clause
                       For foreign keys, use <field_name>_id, not just <fieldname>
            value_fields: iterable of value field names to be used for the updating
                       For foreign keys, use <field_name>_id, not just <fieldname>
            chunk_size: maximum number of rows for a single insert
        """
        if settings.DB_ENGINE_NAME == "sqlite":
            raise ValueError("Sqlite does not support bulk updates")
        self._chunk_size = chunk_size

        self._num_query_values = len(query_fields)
        self._num_values = len(value_fields)

        # create a memoized method to generate sql based on the number of rows to be inserted
        self._generate_sql = memoize(
            self._update_sql_generator(model, query_fields, value_fields)
        )

        self._num_queued_rows = 0

        self._values = []
        self._cursor = connection.cursor()

    def queue_row(self, queries, values):
        """
        Add a row and bulk update if internal queue is larger than CHUNK_SIZE.
        WARNING: Most of the usual Django type conversion magic is bypassed, so the inserted data
        MIGHT look different for anything but simple number/string fields.
        For date/time, always use (timezone) "aware" objects (e.g. datetime.now(tz=utc) with utc
        from django.utils.timezone)
        """
        if len(queries) != self._num_query_values:
            raise ValueError(
                "Not enough keys, expected {}".format(self._num_query_values)
            )

        if len(values) != self._num_values:
            raise ValueError("Not enough values, expected {}".format(self._num_values))

        self._values.extend(queries + values)
        self._num_queued_rows += 1

        if self._num_queued_rows >= self._chunk_size:
            self.update()

    def update(self):
        """
        Triggers the update of previously added rows. This should be done once after all rows
        have been queued.
        """
        if self._num_queued_rows == 0:
            return

        sql = self._generate_sql(self._num_queued_rows)
        self._cursor.execute(sql, self._values)

        self._values = []
        self._num_queued_rows = 0

    def _update_sql_generator(self, model, query_fields, value_fields):
        db_table = model._meta.db_table
        fields = {f.name: f for f in model._meta.fields}
        base_sql = "UPDATE {} SET {} FROM ".format(
            db_table,
            ",".join(
                [
                    "{}=tempvalues.{}".format(value_field, value_field)
                    for value_field in value_fields
                ]
            ),
        )
        # In psycopg2 this was:
        # placeholder_single_row = "({})".format(
        #     (",".join(["%s"] * (len(query_fields) + len(value_fields))))
        # )
        # After the upgrade we have to mimic the update logic in the SQLUpdateCompiler.as_sql
        update_fields = ["%s"] * len(query_fields)  # Retrieve fields
        update_fields += [
            fields[vf].get_placeholder(None, None, connection)
            if hasattr(fields[vf], "get_placeholder")
            else "%s"
            for vf in value_fields
        ]  # Update fields after casting to correct type
        placeholder_single_row = "({})".format(",".join(update_fields))
        single_where_statement = ".".join(["{}".format(db_table), "{}=tempvalues.{}"])
        where_statement_sql = "AS tempvalues ({},{}) WHERE {}".format(
            ",".join([query_field for query_field in query_fields]),
            ",".join([value_field for value_field in value_fields]),
            " AND ".join(
                [
                    single_where_statement.format(query_field, query_field)
                    for query_field in query_fields
                ]
            ),
        )

        def generator(num_rows):
            placeholder_all_rows = "(VALUES {}) ".format(
                ",".join([placeholder_single_row] * num_rows)
            )
            sql_list = [base_sql, placeholder_all_rows, where_statement_sql]

            return "".join(sql_list)

        return generator
