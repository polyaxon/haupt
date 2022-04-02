#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from unittest import TestCase

from django.conf import settings

from common.options.exceptions import OptionException
from common.options.feature import Feature
from common.options.option import NAMESPACE_DB_OPTION_MARKER, OptionStores


class DummyFeature(Feature):
    pass


class TestFeature(TestCase):
    def test_feature_default_store(self):
        assert DummyFeature.store == OptionStores(settings.STORE_OPTION)

    def test_feature_marker(self):
        assert DummyFeature.get_marker() == NAMESPACE_DB_OPTION_MARKER

    def test_parse_key_wtong_namespace(self):
        DummyFeature.key = "FOO"

        with self.assertRaises(OptionException):
            DummyFeature.parse_key()

        DummyFeature.key = "FOO:BAR"

        with self.assertRaises(OptionException):
            DummyFeature.parse_key()

    def test_parse_key_without_namespace(self):
        DummyFeature.key = "FEATURES:FOO"

        assert DummyFeature.parse_key() == (None, "FOO")

    def test_parse_key_with_namespace(self):
        DummyFeature.key = "FEATURES:FOO:BAR"

        assert DummyFeature.parse_key() == ("FOO", "BAR")
