#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from rest_framework import serializers

from haupt.common import conf
from haupt.common.options.registry.k8s import K8S_NAMESPACE


class SettingsMixin:
    settings = serializers.SerializerMethodField()

    def get_settings(self, obj):
        return {"namespace": conf.get(K8S_NAMESPACE)}
