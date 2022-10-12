#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

import os

from email.utils import formatdate
from typing import Dict, Optional

from django.http import FileResponse

from polyaxon.utils.hashing import hash_value


class FilePathResponse(FileResponse):
    def __init__(self, *args, as_attachment=False, filepath="", **kwargs):
        filename = os.path.basename(filepath) if filepath else ""
        headers = self.get_stat_headers(filepath)
        super().__init__(
            open(filepath, mode="rb"),
            *args,
            as_attachment=as_attachment,
            filename=filename,
            headers=headers,
            **kwargs
        )

    def get_stat_headers(self, filepath: str) -> Optional[Dict]:
        if not filepath:
            return
        stat_result = os.stat(filepath)
        last_modified = formatdate(stat_result.st_mtime, usegmt=True)
        etag_base = str(stat_result.st_mtime) + "-" + str(stat_result.st_size)
        etag = hash_value(etag_base.encode(), hash_length=None)

        return {"last-modified": last_modified, "etag": etag}