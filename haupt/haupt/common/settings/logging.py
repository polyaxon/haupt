#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

import os

from typing import Dict


def set_logging(
    context, root_dir: str, log_level: str, log_handlers, debug=False
) -> Dict:
    log_dir = root_dir / "logs"
    context["LOG_DIRECTORY"] = log_dir
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    logging_spec = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "[%(asctime)s] %(levelname)s %(message)s [%(name)s:%(lineno)s]",
                "datefmt": "%d/%b/%Y %H:%M:%S",
            },
            "simple": {"format": "%(levelname)8s  %(message)s [%(name)s]"},
            "verbose": {
                "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"
            },
        },
        "filters": {
            "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}
        },
        "handlers": {
            "logfile": {
                "level": log_level,
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "{}/polyaxon_{}.log".format(log_dir, os.getpid()),
                "maxBytes": 1024 * 1024 * 8,  # 8 MByte
                "backupCount": 5,
                "formatter": "standard",
            },
            "console": {
                "level": log_level,
                "class": "logging.StreamHandler",
                "formatter": "verbose",
            },
        },
        "loggers": {
            "django.request": {
                "propagate": True,
                "handlers": log_handlers,
                "level": log_level,
            },
            "root": {"handlers": log_handlers, "level": log_level},
        },
    }
    if debug:
        logging_spec["loggers"]["django.db.backends"] = {
            "propagate": True,
            "handlers": ["console"],
            "level": log_level,
        }
    context["LOGGING"] = logging_spec
