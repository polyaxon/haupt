#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.


def write_to_conf_file(name, content, path=None, ext: str = "conf"):
    with open("{}/{}.{}".format(path or ".", name, ext), "w") as f:
        f.write(content)
