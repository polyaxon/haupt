from haupt.proxies.schemas.base import get_config

OPTIONS = """
charset utf-8;
"""


def get_charset_config():
    return get_config(options=OPTIONS, indent=0)
