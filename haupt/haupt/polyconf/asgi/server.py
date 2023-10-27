"""
ASGI config for deploy project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

from polyaxon import _dist
from polyaxon._env_vars.keys import ENV_KEYS_SERVICE, ENV_KEYS_SERVICE_MODE
from polyaxon._services.values import PolyaxonServices

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "haupt.polyconf.settings")
os.environ.setdefault("ASGI_APPLICATION", "haupt.polyconf.asgi.server.application")
os.environ[ENV_KEYS_SERVICE] = PolyaxonServices.API
os.environ[ENV_KEYS_SERVICE_MODE] = _dist.CE
application = get_asgi_application()
