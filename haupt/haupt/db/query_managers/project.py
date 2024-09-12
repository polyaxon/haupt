from django.conf import settings

from haupt.db.query_managers import callback_conditions
from haupt.db.query_managers.manager import BaseQueryManager
from polyaxon._pql.builder import (
    ArrayCondition,
    CallbackCondition,
    DateTimeCondition,
    KeysCondition,
    SearchCondition,
    ValueCondition,
)
from polyaxon._pql.parser import (
    parse_datetime_operation,
    parse_search_operation,
    parse_value_operation,
)


class ProjectQueryManager(BaseQueryManager):
    NAME = "project"
    FIELDS_PROXY = {
        "id": "uuid",
        "uid": "uuid",
        "contributors": "contributors__username",
    }
    FIELDS_USE_NAME = {
        "teams",
    }
    FIELDS_ORDERING = (
        "created_at",
        "updated_at",
        "name",
    )
    CHECK_ALIVE = True
    PARSERS_BY_FIELD = {
        # Uuid
        "id": parse_search_operation,
        "uid": parse_search_operation,
        "uuid": parse_search_operation,
        # Dates
        "created_at": parse_datetime_operation,
        "updated_at": parse_datetime_operation,
        # Name
        "name": parse_search_operation,
        # Description
        "description": parse_search_operation,
        # Tags
        "tags": parse_value_operation,
        # Live state
        "live_state": parse_value_operation,
        # Teams
        "teams": parse_value_operation,
        # Contributors
        "contributors": parse_value_operation,
        # Kind
        "kind": parse_value_operation,
    }
    CONDITIONS_BY_FIELD = {
        # Uuid
        "id": SearchCondition,
        "uid": SearchCondition,
        "uuid": SearchCondition,
        # Dates
        "created_at": DateTimeCondition,
        "updated_at": DateTimeCondition,
        # Name
        "name": SearchCondition,
        # Description
        "description": SearchCondition,
        # Tags
        "tags": KeysCondition
        if settings.DB_ENGINE_NAME == "sqlite"
        else ArrayCondition,
        # Live state
        "live_state": ValueCondition,
        # Teams
        "teams": ValueCondition,
        # Contributors
        "contributors": ValueCondition,
        # Kind
        "kind": CallbackCondition(callback_conditions.project_kind_condition),
    }
