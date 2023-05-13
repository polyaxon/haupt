import os

import aiofiles
import nbformat

from asgiref.sync import sync_to_async
from nbconvert import HTMLExporter


async def render_notebook(archived_path: str, check_cache=True):
    html_path = archived_path.split(".ipynb")[0] + ".html"
    if os.path.exists(html_path):
        if check_cache:
            # file already exists
            return html_path
        else:
            os.remove(html_path)

    async with aiofiles.open(os.path.abspath(archived_path), mode="r") as f:
        read_data = await f.read()
        notebook = await sync_to_async(nbformat.reads)(read_data, as_version=4)
        html_exporter = HTMLExporter()
        (body, resources) = await sync_to_async(html_exporter.from_notebook_node)(
            notebook
        )
        html_file = "<style>" + resources["inlining"]["css"][0] + "</style>" + body
        async with aiofiles.open(html_path, "w") as destination:
            await destination.write(html_file)
        return html_path
