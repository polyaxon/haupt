import tempfile

from django.conf import settings
from django.core.cache import cache
from django.test import TestCase


class PolyaxonBaseTest(TestCase):
    COLLECT_TASKS = False

    def setUp(self):
        # Flush cache
        cache.clear()
        # Mock celery default sent task
        self.mock_send_task()
        super().setUp()
        self.worker_send = {}
        settings.ARTIFACTS_ROOT = tempfile.mkdtemp()
        settings.ARCHIVES_ROOT = tempfile.mkdtemp()

    def mock_send_task(self):
        from celery import current_app

        def send_task(name, args=(), kwargs=None, **opts):
            kwargs = kwargs or {}
            if name in current_app.tasks:
                task = current_app.tasks[name]
                return task.apply_async(args, kwargs, **opts)
            elif self.worker_send:
                self.worker_send[name] = {"args": args, "kwargs": kwargs, "opts": opts}

        current_app.send_task = send_task


class PolyaxonBaseTestSerializer(PolyaxonBaseTest):
    query = None
    serializer_class = None
    model_class = None
    factory_class = None
    expected_keys = {}
    num_objects = 2

    def test_serialize_one(self):
        raise NotImplementedError

    def create_one(self):
        raise NotImplementedError

    def create_multiple(self):
        for i in range(self.num_objects):
            self.create_one()

    def test_serialize_many(self):
        self.create_multiple()
        data = self.serializer_class(self.query.all(), many=True).data
        assert len(data) == self.num_objects
        for d in data:
            assert set(d.keys()) == self.expected_keys
