from haupt.proxies.schemas.base import get_config

OPTIONS = """
location = /robots.txt {{
    rewrite ^ /static/robots.txt;
}}
"""


def get_robots_config():
    return get_config(options=OPTIONS, indent=0)
