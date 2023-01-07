#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from unittest import TestCase

from haupt.common.events.event import Attribute, Event
from haupt.common.events.event_manager import EventManager
from haupt.common.events.event_service import EventService


class DummyEventService(EventService):
    def __init__(self):
        self.events = []
        super().__init__()

    def record_event(self, event):
        self.events.append(event)


class DummyEvent(Event):
    event_type = "dummy.event"
    attributes = (Attribute("dummy_attr"), Attribute("new_attr", is_required=False))


class DummyObject:
    def __init__(self, dummy_attr):
        self.dummy_attr = dummy_attr


class TestEventService(TestCase):
    def setUp(self):
        self.service = DummyEventService()
        self.service.event_manager = EventManager()
        self.service.setup()
        super().setUp()

    def test_can_handle(self):
        # Test handles only str event types
        assert self.service.can_handle(event_type=1) is False

        # The service's manager did not subscribe to the event yet
        assert self.service.can_handle(event_type=DummyEvent.event_type) is False

        # Subscribe to the event
        self.service.event_manager.subscribe(DummyEvent)
        assert self.service.can_handle(event_type=DummyEvent.event_type) is True

    def test_record(self):
        # The service's manager did not subscribe to the event yet
        assert self.service.record(event_type=DummyEvent.event_type) is None

        # Subscribe
        self.service.event_manager.subscribe(DummyEvent)
        dummy_instance = DummyObject(dummy_attr="test1")
        self.service.record(event_type=DummyEvent.event_type, instance=dummy_instance)

        assert len(self.service.events) == 1
        event = self.service.events.pop(0)
        assert event.event_type == DummyEvent.event_type
        assert event.datetime is not None
        assert event.data["dummy_attr"] == dummy_instance.dummy_attr
        assert event.data["new_attr"] is None

    def test_record_with_args(self):
        self.service.event_manager.subscribe(DummyEvent)
        dummy_instance = DummyObject(dummy_attr="test2")
        self.service.record(
            event_type=DummyEvent.event_type,
            instance=dummy_instance,
            new_attr="new_attr",
        )

        assert len(self.service.events) == 1
        event = self.service.events.pop(0)
        assert event.event_type == DummyEvent.event_type
        assert event.datetime is not None
        assert event.data["dummy_attr"] == dummy_instance.dummy_attr
        assert event.data["new_attr"] == "new_attr"
