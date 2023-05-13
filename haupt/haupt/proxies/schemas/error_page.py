from haupt.proxies.schemas.base import get_config

OPTIONS = """
error_page 500 502 503 504 /static/errors/50x.html;
error_page 401 403 /static/errors/permission.html;
error_page 404 /static/errors/404.html;
"""


def get_error_page_config():
    return get_config(options=OPTIONS, indent=0)
