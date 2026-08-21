from email.utils import formatdate
import os
from typing import Dict, Optional

from django.http import FileResponse

from clipped.utils.hashing import hash_value


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
            **kwargs,
        )

    def get_stat_headers(self, filepath: str) -> Optional[Dict]:
        if not filepath:
            return
        stat_result = os.stat(filepath)
        last_modified = formatdate(stat_result.st_mtime, usegmt=True)
        etag_base = str(stat_result.st_mtime) + "-" + str(stat_result.st_size)
        etag = hash_value(etag_base.encode(), hash_length=None)

        return {"last-modified": last_modified, "etag": etag}
