from django.conf import settings
from django.db.models import Q

from polyaxon._pql.manager import PQLManager


class BaseQueryManager(PQLManager):
    QUERY_BACKEND = Q
    TIMEZONE = settings.TIME_ZONE
