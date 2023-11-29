import uuid

from django.contrib.auth import get_user_model

from haupt.common import conf
from haupt.common.options.registry.installation import ORGANIZATION_ID
from haupt.db.abstracts.projects import Owner


def get_dummy_key():
    first_joined = get_user_model().objects.order_by("date_joined").first()
    if first_joined:
        key = uuid.uuid5(Owner.uuid, str(first_joined.date_joined.timestamp())).hex
    else:
        key = uuid.uuid4().hex
    conf.set(ORGANIZATION_ID, key)
    return key
