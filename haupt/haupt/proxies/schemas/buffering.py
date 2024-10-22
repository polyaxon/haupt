from haupt.proxies.schemas.base import get_config

OPTIONS = """
client_max_body_size        0;
client_body_buffer_size     50m;
client_body_in_file_only clean;
large_client_header_buffers 8 1m;
client_header_buffer_size 1m;
uwsgi_buffer_size 1m;
uwsgi_buffers 8 1m;
uwsgi_busy_buffers_size 2m;
sendfile on;
"""


def get_buffering_config():
    return get_config(options=OPTIONS, indent=0)
