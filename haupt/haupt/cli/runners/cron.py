import atexit
import logging
import threading
import time

from haupt.streams.connections.fs import AppFS
from polyaxon._constants.globals import DEFAULT, NO_AUTH
from polyaxon._fs.fs import get_sync_default_fs
from polyaxon._fs.manager import delete_file_or_dir
from polyaxon._fs.utils import get_store_path
from polyaxon._schemas.client import ClientConfig
from polyaxon.client import PolyaxonClient
from polyaxon.exceptions import ApiException
from urllib3.exceptions import HTTPError

_logger = logging.getLogger("haupt.cli.cron")


def agent_cron(host, stop_event: threading.Event):
    config = ClientConfig(host=host, token=NO_AUTH)
    polyaxon_client = PolyaxonClient(config=config)
    time.sleep(5)
    fs = get_sync_default_fs()
    store_path = AppFS.get_fs_root_path()
    while not stop_event.is_set():
        try:
            agent_state = polyaxon_client.agents_v1.cron_agent(
                owner=DEFAULT, _request_timeout=10, body={"state": True}
            )
            if agent_state and agent_state.state:
                deleting = agent_state.state.deleting or []
                for deleting_path in deleting:
                    subpath = get_store_path(
                        store_path=store_path, subpath=deleting_path
                    )
                    delete_file_or_dir(
                        fs=fs,
                        subpath=subpath,
                        is_file=False,
                    )
        except (ApiException, HTTPError) as e:
            _logger.debug(e)
            _logger.info("Waiting for Polyaxon to be ready...")
            time.sleep(5)
        time.sleep(2)


def start_cron(host: str):
    stop_event = threading.Event()
    thread = threading.Thread(
        target=agent_cron,
        args=(
            host,
            stop_event,
        ),
    )
    thread.daemon = True
    thread.start()

    # Ensure the thread stops gracefully on exit
    atexit.register(stop_event.set)
