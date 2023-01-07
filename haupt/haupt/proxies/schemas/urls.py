#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from urllib.parse import urlparse


def get_service_url(host: str, port: int):
    if port == 80:
        return "http://{}".format(host)
    if port == 443:
        return "https://{}".format(host)
    return "http://{}:{}".format(host, port)


def has_https(url: str):
    return "https" in url


def get_ssl_server_name(url: str):
    if has_https(url):
        return "proxy_ssl_server_name on;"
    return ""


def get_header_host(url: str):
    if has_https(url):
        return "proxy_set_header Host {};".format(urlparse(url).netloc.split(":")[0])
    return "proxy_set_header Host $http_host;"


def get_service_proxy(port: int = 8443):
    return "https://127.0.0.1:{}".format(port)
