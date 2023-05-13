from haupt.proxies.schemas.base import get_config

OPTIONS = """
location = /favicon.ico {{
    rewrite ^ /static/images/favicon.ico;
}}
"""


def get_favicon_config():
    return get_config(options=OPTIONS, indent=0)
