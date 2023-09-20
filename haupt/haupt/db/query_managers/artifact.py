from haupt.db.query_managers.manager import BaseQueryManager
from polyaxon._pql.builder import BoolCondition, SearchCondition, ValueCondition
from polyaxon._pql.parser import parse_search_operation, parse_value_operation


class ArtifactQueryManager(BaseQueryManager):
    NAME = "artifact"
    FIELDS_ORDERING = ("name", "kind", "path", "is_input")
    FIELDS_USE_UUID = {"run"}
    FIELDS_PROXY = {
        "id": "name",
        "name": "artifact__name",
        "kind": "artifact__kind",
        "path": "artifact__path",
        "state": "artifact__state",
    }
    CHECK_ALIVE = False
    PARSERS_BY_FIELD = {
        # Name
        "name": parse_search_operation,
        # Kind
        "kind": parse_value_operation,
        # Path
        "path": parse_value_operation,
        # State
        "state": parse_value_operation,
        # Is input
        "is_input": parse_value_operation,
        # Run
        "run": parse_value_operation,
    }
    CONDITIONS_BY_FIELD = {
        # Name
        "name": SearchCondition,
        # Kind
        "kind": ValueCondition,
        # Path
        "path": ValueCondition,
        # State
        "state": ValueCondition,
        # Is input
        "is_input": BoolCondition,
        # Run
        "run": ValueCondition,
    }
