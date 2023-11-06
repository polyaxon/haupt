from haupt.db.query_managers.manager import BaseQueryManager
from polyaxon._pql.builder import (
    ArrayCondition,
    DateTimeCondition,
    SearchCondition,
    ValueCondition,
)
from polyaxon._pql.parser import (
    parse_datetime_operation,
    parse_search_operation,
    parse_value_operation,
)


class ProjectVersionQueryManager(BaseQueryManager):
    NAME = "project_version"
    FIELDS_USE_NAME = {
        "project",
    }
    FIELDS_PROXY = {
        "id": "uuid",
        "uid": "uuid",
        "teams": "project__teams__name",
    }
    FIELDS_ORDERING = (
        "created_at",
        "updated_at",
        "name",
        "uuid",
        "state",
        "stage",
        "kind",
    )
    FIELDS_USE_UUID = {
        "run",
    }
    CHECK_ALIVE = False
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
        # Kind
        "kind": parse_value_operation,
        # State
        "state": parse_value_operation,
        # Stage
        "stage": parse_value_operation,
        # Run
        "run": parse_value_operation,
        # Teams
        "teams": parse_value_operation,
        # Projects
        "project": parse_value_operation,
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
        "tags": ArrayCondition,
        # Kind
        "kind": ValueCondition,
        # State
        "state": ValueCondition,
        # Stage
        "stage": ValueCondition,
        # Run
        "run": ValueCondition,
        # Teams
        "teams": ValueCondition,
        # Projects
        "project": ValueCondition,
    }
