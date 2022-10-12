#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
from haupt.proxies.schemas.base import get_config
from polyaxon.api import STREAMS_V1_LOCATION

API_OPTIONS = """
location / {{
    proxy_pass http://polyaxon;
    proxy_http_version 1.1;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_intercept_errors {intercept_errors};
}}
"""


def get_api_config():
    return get_config(options=API_OPTIONS, indent=0, intercept_errors="off")


K8S_AUTH_OPTIONS = """
location {app}k8s/auth/ {{
    proxy_method      GET;
    proxy_pass http://polyaxon;
    proxy_http_version 1.1;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Origin "";
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Origin-URI $request_uri;
    proxy_intercept_errors {intercept_errors};
}}
"""


def get_k8s_auth_config():
    return get_config(
        options=K8S_AUTH_OPTIONS,
        app=STREAMS_V1_LOCATION,
        indent=0,
        intercept_errors="off",
    )
