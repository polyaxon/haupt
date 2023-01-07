#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.


class UniqueNameMixin:
    """
    A mixin to force setting a unique name.
    """

    @property
    def unique_name(self) -> str:
        raise NotImplementedError
