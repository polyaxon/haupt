import os

from typing import Dict

from haupt.schemas.platform_config import PlatformConfig


def set_logging(
    context,
    config: PlatformConfig,
) -> Dict:
    context["LOG_DIRECTORY"] = config.logs_root
    if not os.path.exists(config.logs_root):
        os.makedirs(config.logs_root)
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
                "level": config.log_level,
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "{}/polyaxon_{}.log".format(config.logs_root, os.getpid()),
                "maxBytes": 1024 * 1024 * 8,  # 8 MByte
                "backupCount": 5,
                "formatter": "standard",
            },
            "console": {
                "level": config.log_level,
                "class": "logging.StreamHandler",
                "formatter": "verbose",
            },
        },
        "loggers": {
            "django.request": {
                "propagate": True,
                "handlers": ["console"],
                "level": config.log_level,
            },
            "root": {"handlers": ["console"], "level": config.log_level},
        },
    }
    if config.is_debug_mode:
        logging_spec["loggers"]["django.db.backends"] = {
            "propagate": True,
            "handlers": ["console"],
            "level": config.log_level,
        }
    context["LOGGING"] = logging_spec
