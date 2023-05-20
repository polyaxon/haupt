from clipped.decorators.memoization import memoize

from django.db import connection


class RawBulkInserter:
    """
    This class does bulk inserts similar to Django's bulk_create, but does not use model instances.
    This can save a significant amount of time for very large inserts (e.g. > 100k values)
    IMPORTANT: Since all of the ORM magic is bypassed, you have to be careful with the types of
    the values you pass.
    """

    def __init__(
        self, model, fields, chunk_size=40000, fetch_ids=False, table_name=None
    ):
        """
        Params:
            model: model class
            fields: iterable of field names to be used for inserts
                For foreign keys, use <field_name>_id, not just <fieldname>
            chunk_size: maximum number of rows for a single insert
            fetch_ids: if True, add_row and insert will return a list of created ids
                Requires that the model has an 'id' column
        """
        self._chunk_size = chunk_size
        self._fetch_ids = fetch_ids
        if fetch_ids:
            self._created_ids = []

        self._num_fields = len(fields)

        if model is not None:
            table_name = model._meta.db_table

        # create a memoized method to generate sql based on the number of rows to be inserted
        self._generate_sql = memoize(
            self._create_sql_generator(table_name, fields, fetch_ids)
        )

        self._num_queued_rows = 0

        self._values = []
        self._cursor = connection.cursor()

    def queue_row(self, *values):
        """
        Add a row and bulk insert if internal queue is larger than CHUNK_SIZE.
        WARNING: Most of the usual Django type conversion magic is bypassed, so the inserted data
        MIGHT look different for anything but simple number/string fields.
        For date/time, always use (timezone) "aware" objects (e.g. datetime.now(tz=utc) with utc
        from django.utils.timezone)
        """
        if len(values) != self._num_fields:
            raise ValueError("Not enough values, expected {}".format(self._num_fields))

        self._values.extend(values)
        self._num_queued_rows += 1

        if self._num_queued_rows >= self._chunk_size:
            self.insert()

    def insert(self):
        """
        Triggers the insertion of previously added rows. This should be done once after all rows
        have been queued.
        """
        if self._num_queued_rows == 0:
            return

        self._cursor.execute(self._generate_sql(self._num_queued_rows), self._values)

        if self._fetch_ids:
            rows = self._cursor.fetchall()
            self._created_ids.extend([row[0] for row in rows])

        self._values = []
        self._num_queued_rows = 0

    @property
    def all_created_ids(self):
        """
        Id's of all created rows, in the same order as the rows were queued (-> queue_row)
        Requires fetch_ids=True in the constructor.
        IMPORTANT: May be empty/incomplete before full insert is triggered by insert()
        """
        return self._created_ids

    @staticmethod
    def _create_sql_generator(table_name, fields, fetch_ids):
        # escape field names that contain a '%'
        fields = [field.replace("%", "%%") for field in fields]

        base_sql = 'INSERT INTO {} ("{}") VALUES '.format(
            table_name, '","'.join(fields)
        )
        placeholder_single_row = "({})".format((",".join(["%s"] * len(fields))))

        def generator(num_rows):
            sql_list = [base_sql, ",".join([placeholder_single_row] * num_rows)]
            if fetch_ids:
                sql_list.append(" RETURNING id")

            return "".join(sql_list)

        return generator
