"""
ASGI config for deploy project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
"""
import logging
import os

from django.core.asgi import get_asgi_application

from haupt import settings
from polyaxon._contexts import paths as ctx_paths
from polyaxon._env_vars.keys import (
    ENV_KEYS_SANDBOX_ROOT,
    ENV_KEYS_SERVICE,
    ENV_KEYS_SERVICE_MODE,
    ENV_KEYS_UI_IN_SANDBOX,
)
from polyaxon._services.values import PolyaxonServices

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "haupt.polyconf.settings")
os.environ.setdefault("ASGI_APPLICATION", "haupt.polyconf.asgi.viewer.application")
os.environ[ENV_KEYS_SERVICE] = PolyaxonServices.STREAMS
os.environ[ENV_KEYS_SERVICE_MODE] = PolyaxonServices.VIEWER
os.environ[ENV_KEYS_UI_IN_SANDBOX] = "true"
logging.warning(os.environ.get(ENV_KEYS_SANDBOX_ROOT, ctx_paths.CONTEXT_OFFLINE_ROOT))
settings.set_sandbox_config(
    path=os.environ.get(ENV_KEYS_SANDBOX_ROOT, ctx_paths.CONTEXT_OFFLINE_ROOT),
    env_only_config=True,
)
application = get_asgi_application()
