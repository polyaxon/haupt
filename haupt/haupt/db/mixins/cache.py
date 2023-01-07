#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.


class CachedMixin:
    """
    A mixin to help clear cached properties.
    """

    CACHED_PROPERTIES = ()

    def clear_cached_properties(self, properties=None):
        properties = properties or self.CACHED_PROPERTIES
        for key in properties:
            if key in self.__dict__:
                del self.__dict__[key]
