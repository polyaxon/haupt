import atexit
import logging
import threading
import time

from polyaxon._constants.globals import DEFAULT, NO_AUTH
from polyaxon._schemas.client import ClientConfig
from polyaxon.client import PolyaxonClient
from polyaxon.exceptions import ApiException
from urllib3.exceptions import HTTPError

_logger = logging.getLogger("haupt.cli.cron")


def agent_cron(host, stop_event: threading.Event):
    config = ClientConfig(host=host, token=NO_AUTH)
    polyaxon_client = PolyaxonClient(config=config)
    time.sleep(5)
    while not stop_event.is_set():
        try:
            polyaxon_client.agents_v1.cron_agent(owner=DEFAULT, _request_timeout=10)
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
