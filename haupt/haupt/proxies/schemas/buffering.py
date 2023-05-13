from haupt.proxies.schemas.base import get_config

OPTIONS = """
client_max_body_size        0;
client_body_buffer_size     50m;
client_body_in_file_only clean;
sendfile on;
"""


def get_buffering_config():
    return get_config(options=OPTIONS, indent=0)
