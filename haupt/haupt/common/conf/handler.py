#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from typing import Any, Dict, Optional

from haupt.common.options.option import Option


class BaseConfHandler:
    def get(self, option: Option, owners: Optional[Dict[str, int]] = None) -> Any:
        raise NotImplementedError

    def set(self, option: Option, value: Any, owners: Optional[Dict[str, int]] = None):
        raise NotImplementedError

    def delete(self, option: Option, owners: Optional[Dict[str, int]] = None) -> Any:
        raise NotImplementedError
