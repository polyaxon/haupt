#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from unittest import TestCase

from common.conf.exceptions import ConfException
from common.conf.handlers.env_handler import EnvConfHandler
from common.options.option import Option, OptionScope, OptionStores
from polyaxon import types


class DummyEnvOption(Option):
    key = "FOO_BAR1"
    scope = OptionScope.GLOBAL
    is_secret = False
    is_optional = True
    is_list = False
    store = OptionStores.ENV
    typing = types.INT
    default = None
    options = None


class DummyOptionalDefaultEnvOption(Option):
    key = "FOO_BAR2"
    scope = OptionScope.GLOBAL
    is_secret = False
    is_optional = True
    is_list = False
    store = OptionStores.ENV
    typing = types.STR
    default = "default_env"
    options = None


class DummyNonOptionalEnvOption(Option):
    key = "FOO_BAR3"
    scope = OptionScope.GLOBAL
    is_secret = False
    is_optional = False
    is_list = False
    store = OptionStores.ENV
    typing = types.INT
    default = None
    options = None


class DummySecretEnvOption(Option):
    key = "FOO_BAR4"
    scope = OptionScope.GLOBAL
    is_secret = True
    is_optional = False
    is_list = False
    store = OptionStores.ENV
    typing = types.INT
    default = None
    options = None


class TestClusterOptionsHandler(TestCase):
    def setUp(self):
        super().setUp()
        self.env_options_handler = EnvConfHandler()

    def test_get_default_value(self):
        assert self.env_options_handler.get(DummyEnvOption) is None
        assert (
            self.env_options_handler.get(DummyOptionalDefaultEnvOption) == "default_env"
        )
        with self.assertRaises(ConfException):
            self.env_options_handler.get(DummyNonOptionalEnvOption)
        with self.assertRaises(ConfException):
            self.env_options_handler.get(DummySecretEnvOption)

    def test_set_get_delete_value(self):
        self.env_options_handler.set(DummyEnvOption, 123)
        self.env_options_handler.set(DummyOptionalDefaultEnvOption, 123)
        self.env_options_handler.set(DummyNonOptionalEnvOption, 123)
        self.env_options_handler.set(DummySecretEnvOption, 123)

        assert self.env_options_handler.get(DummyEnvOption) == 123
        assert self.env_options_handler.get(DummyOptionalDefaultEnvOption) == "123"
        assert self.env_options_handler.get(DummyNonOptionalEnvOption) == 123
        assert self.env_options_handler.get(DummySecretEnvOption) == 123

        self.env_options_handler.delete(DummyEnvOption)
        self.env_options_handler.delete(DummyOptionalDefaultEnvOption)
        self.env_options_handler.delete(DummyNonOptionalEnvOption)
        self.env_options_handler.delete(DummySecretEnvOption)

        assert self.env_options_handler.get(DummyEnvOption) is None
        assert (
            self.env_options_handler.get(DummyOptionalDefaultEnvOption) == "default_env"
        )
        with self.assertRaises(ConfException):
            self.env_options_handler.get(DummyNonOptionalEnvOption)
        with self.assertRaises(ConfException):
            self.env_options_handler.get(DummySecretEnvOption)
