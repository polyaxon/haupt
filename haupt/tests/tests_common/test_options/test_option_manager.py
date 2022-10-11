#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from unittest import TestCase

from haupt.common.options.option_manager import OptionManager
from haupt.common.options.registry.core import CeleryBrokerUrl, Logging


class TestOptionManager(TestCase):
    def setUp(self):
        self.manager = OptionManager()
        super().setUp()

    def test_subscribe(self):
        self.assertEqual(len(self.manager.state), 0)
        self.manager.subscribe(CeleryBrokerUrl)
        assert len(self.manager.state) == 1
        assert len(self.manager.items) == 1
        assert len(self.manager.keys) == 1
        assert len(self.manager.values) == 1
        assert CeleryBrokerUrl.key in self.manager.state
        assert self.manager.state[CeleryBrokerUrl.key] == CeleryBrokerUrl

        # Adding the same event
        self.manager.subscribe(CeleryBrokerUrl)
        assert len(self.manager.state) == 1
        assert len(self.manager.items) == 1
        assert len(self.manager.items) == 1
        assert len(self.manager.keys) == 1
        assert len(self.manager.values) == 1

        # Adding new event
        self.manager.subscribe(Logging)
        assert len(self.manager.state) == 2
        assert len(self.manager.items) == 2
        assert len(self.manager.items) == 2
        assert len(self.manager.keys) == 2
        assert len(self.manager.values) == 2

        # Adding new event with same event type
        class DummyEvent(Logging):
            pass

        with self.assertRaises(AssertionError):
            self.manager.subscribe(DummyEvent)

    def test_knows(self):
        assert self.manager.knows(key=CeleryBrokerUrl.key) is False
        self.manager.subscribe(CeleryBrokerUrl)
        assert self.manager.knows(key=CeleryBrokerUrl.key) is True

        # Adding same event
        self.manager.subscribe(CeleryBrokerUrl)
        assert self.manager.knows(key=CeleryBrokerUrl.key) is True

        # New event
        assert self.manager.knows(Logging) is False
        self.manager.subscribe(Logging)
        assert self.manager.knows(key=Logging.key) is True

    def test_get(self):
        assert self.manager.get(key=CeleryBrokerUrl.key) is None
        self.manager.subscribe(CeleryBrokerUrl)
        assert self.manager.get(key=CeleryBrokerUrl.key) == CeleryBrokerUrl
