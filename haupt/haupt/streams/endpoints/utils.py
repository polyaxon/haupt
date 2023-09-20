import os

from typing import Dict, Optional, Union

from rest_framework import status

from django.core.handlers.asgi import ASGIRequest
from django.http import FileResponse, HttpResponse

from aiofiles.os import stat as aio_stat
from haupt.common.endpoints.files import FilePathResponse
from polyaxon._services.values import PolyaxonServices


async def _redirect(
    redirect_path: str, is_file: bool = False, additional_headers: Optional[Dict] = None
) -> HttpResponse:
    headers = {"Content-Type": "", "X-Accel-Redirect": redirect_path}
    if additional_headers:
        headers.update(additional_headers)
    if is_file:
        stat_result = await aio_stat(redirect_path)
        headers["X-Content-Length"] = str(stat_result.st_size)
        headers["Content-Disposition"] = 'attachment; filename="{}"'.format(
            os.path.basename(redirect_path)
        )

    return HttpResponse(headers=headers)


async def redirect_file(
    archived_path: str, additional_headers: Optional[Dict] = None
) -> Union[HttpResponse, FileResponse]:
    if not archived_path:
        return HttpResponse(
            content="Artifact not found: filepath={}",
            status=status.HTTP_404_NOT_FOUND,
        )

    if PolyaxonServices.is_sandbox():
        return FilePathResponse(filepath=archived_path)
    return await _redirect(
        redirect_path=archived_path, is_file=True, additional_headers=additional_headers
    )


async def redirect_api(
    redirect_path: str, additional_headers: Optional[Dict] = None
) -> HttpResponse:
    if not redirect_path:
        return HttpResponse(
            content="API not found",
            status=status.HTTP_404_NOT_FOUND,
        )

    return await _redirect(
        redirect_path=redirect_path,
        is_file=False,
        additional_headers=additional_headers,
    )


def inject_auth_header(request: ASGIRequest, headers: Dict) -> Dict:
    auth = request.headers.get("Authorization")
    if auth:
        headers["Authorization"] = auth
    return headers
