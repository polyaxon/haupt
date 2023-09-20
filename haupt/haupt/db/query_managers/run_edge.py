from django.conf import settings

from haupt.db.query_managers.manager import BaseQueryManager
from polyaxon._pql.builder import ArrayCondition, KeysCondition, ValueCondition
from polyaxon._pql.parser import parse_value_operation


class RunEdgeQueryManager(BaseQueryManager):
    NAME = "run_edge"
    FIELDS_ORDERING = (
        "kind",
        "upstream",
        "downstream",
    )
    FIELDS_USE_UUID = {"upstream", "downstream"}
    FIELDS_PROXY = {
        "id": "uuid",
        "uid": "uuid",
    }
    FIELDS_ORDERING_PROXY = {
        "values": {"field": "values", "annotate": True},
    }
    CHECK_ALIVE = False
    PARSERS_BY_FIELD = {
        # upstream
        "upstream": parse_value_operation,
        # downstream
        "downstream": parse_value_operation,
        # Kind
        "kind": parse_value_operation,
        # Status
        "statuses": parse_value_operation,
        # Values
        "values": parse_value_operation,
    }
    CONDITIONS_BY_FIELD = {
        # upstream
        "upstream": ValueCondition,
        # downstream
        "downstream": ValueCondition,
        # Kind
        "kind": ValueCondition,
        # Status
        "statuses": KeysCondition
        if settings.DB_ENGINE_NAME == "sqlite"
        else ArrayCondition,
        # Values
        "values": ValueCondition,
    }
