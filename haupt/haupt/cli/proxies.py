import os

import click


@click.command()
@click.argument("component")
@click.option(
    "--path", default="./web", help="Path where the config should be generated."
)
@click.option("--root", help="Absolute root where the configs, default to pwd")
def proxy(component, path, root):
    """Create api proxy."""
    from haupt import settings
    from haupt.proxies.generators import (
        generate_api_conf,
        generate_forward_proxy_cmd,
        generate_gateway_conf,
        generate_streams_conf,
    )
    from haupt.settings import set_proxies_config
    from polyaxon._services.values import PolyaxonServices
    from polyaxon.exceptions import PolyaxonException

    if not root:
        root = os.path.abspath(".")

    set_proxies_config()

    if PolyaxonServices.is_api(component):
        generate_api_conf(path=path, root=root)
    elif PolyaxonServices.is_streams(component):
        generate_streams_conf(path=path, root=root)
        generate_forward_proxy_cmd(path=path)
    elif PolyaxonServices.is_gateway(component):
        generate_gateway_conf(path=path, root=root)
        generate_forward_proxy_cmd(path=path)
    else:
        raise PolyaxonException("Component {} is not recognized".format(component))

    if not os.path.exists(settings.PROXIES_CONFIG.logs_root):
        os.makedirs(settings.PROXIES_CONFIG.logs_root)
