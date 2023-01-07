#!/usr/bin/python
#
# Copyright 2018-2023 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

try:
    from django.utils.crypto import salted_hmac
except ImportError:
    raise ImportError("This module depends on django.")


def get_hmac(key_salt, value):
    return salted_hmac(key_salt, value).hexdigest()
