#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from haupt import settings
from haupt.proxies.schemas.base import get_config
from haupt.proxies.schemas.urls import get_service_url

STREAMS_OPTIONS = r"""
location /streams/ {{
    {auth}
    {resolver}
    proxy_pass {service};
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}}
"""  # noqa


def get_streams_location_config(resolver: str, auth: str):
    service = get_service_url(
        host=settings.PROXIES_CONFIG.streams_host,
        port=settings.PROXIES_CONFIG.streams_port,
    )
    return get_config(
        options=STREAMS_OPTIONS, resolver=resolver, auth=auth, service=service
    )


K8S_OPTIONS = r"""
location /k8s/ {{
    {auth}
    {resolver}
    proxy_pass {service};
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_buffering off;
}}
"""  # noqa


def get_k8s_location_config(resolver: str, auth: str):
    service = get_service_url(
        host=settings.PROXIES_CONFIG.streams_host,
        port=settings.PROXIES_CONFIG.streams_port,
    )
    return get_config(
        options=K8S_OPTIONS, resolver=resolver, auth=auth, service=service
    )
