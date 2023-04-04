#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
from typing import Optional


def write_to_conf_file(
    name: str, content: str, path: Optional[str] = None, ext: str = "conf"
):
    with open("{}/{}.{}".format(path or ".", name, ext), "w") as f:
        f.write(content)
