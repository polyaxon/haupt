#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from unittest import TestCase

from common.events.event_manager import EventManager
from common.events.registry.run import (
    RunCreatedActorEvent,
    RunCreatedEvent,
    RunDeletedActorEvent,
    RunStoppedEvent,
    RunViewedActorEvent,
)


class TestEventManager(TestCase):
    def setUp(self):
        self.manager = EventManager()
        super().setUp()

    def test_subscribe(self):
        self.assertEqual(len(self.manager.state), 0)
        self.manager.subscribe(RunCreatedEvent)
        assert len(self.manager.state) == 1
        assert len(self.manager.items) == 1
        assert len(self.manager.keys) == 1
        assert len(self.manager.values) == 1
        assert RunCreatedEvent.event_type in self.manager.state
        assert self.manager.state[RunCreatedEvent.event_type] == RunCreatedEvent

        # Adding the same event
        self.manager.subscribe(RunCreatedEvent)
        assert len(self.manager.state) == 1
        assert len(self.manager.items) == 1
        assert len(self.manager.items) == 1
        assert len(self.manager.keys) == 1
        assert len(self.manager.values) == 1

        # Adding new event
        self.manager.subscribe(RunStoppedEvent)
        assert len(self.manager.state) == 2
        assert len(self.manager.items) == 2
        assert len(self.manager.items) == 2
        assert len(self.manager.keys) == 2
        assert len(self.manager.values) == 2

        # Adding new event with same event type
        class DummyEvent(RunCreatedEvent):
            pass

        with self.assertRaises(AssertionError):
            self.manager.subscribe(DummyEvent)

    def test_knows(self):
        assert self.manager.knows(event_type=RunCreatedEvent.event_type) is False
        self.manager.subscribe(RunCreatedEvent)
        assert self.manager.knows(event_type=RunCreatedEvent.event_type) is True

        # Adding same event
        self.manager.subscribe(RunCreatedEvent)
        assert self.manager.knows(event_type=RunCreatedEvent.event_type) is True

        # New event
        assert self.manager.knows(RunCreatedEvent) is False
        self.manager.subscribe(RunCreatedEvent)
        assert self.manager.knows(event_type=RunCreatedEvent.event_type) is True

    def test_get(self):
        assert self.manager.get(event_type=RunCreatedEvent.event_type) is None
        self.manager.subscribe(RunCreatedEvent)
        assert (
            self.manager.get(event_type=RunCreatedEvent.event_type) == RunCreatedEvent
        )

    def test_user_write_events(self):
        assert self.manager.user_write_events() == []
        self.manager.subscribe(RunViewedActorEvent)
        assert self.manager.user_write_events() == []
        self.manager.subscribe(RunStoppedEvent)
        assert self.manager.user_write_events() == []
        self.manager.subscribe(RunDeletedActorEvent)
        assert self.manager.user_write_events() == [RunDeletedActorEvent.event_type]
        self.manager.subscribe(RunCreatedActorEvent)
        assert self.manager.user_write_events() == [
            RunDeletedActorEvent.event_type,
            RunCreatedActorEvent.event_type,
        ]

    def test_user_view_events(self):
        assert self.manager.user_view_events() == []
        self.manager.subscribe(RunCreatedEvent)
        assert self.manager.user_view_events() == []
        self.manager.subscribe(RunCreatedEvent)
        assert self.manager.user_view_events() == []
        self.manager.subscribe(RunStoppedEvent)
        assert self.manager.user_view_events() == []
        self.manager.subscribe(RunViewedActorEvent)
        assert self.manager.user_view_events() == [RunViewedActorEvent.event_type]
