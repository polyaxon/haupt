from typing import Any, Optional, Tuple

from haupt.common.service_interface import Service
from polyaxon.exceptions import PQLException
from polyaxon.pql.manager import PQLManager
from polyaxon.pql.parser import parse_field


class QueryService(Service):
    __all__ = ("filter_queryset", "parse_field")

    @classmethod
    def filter_queryset(
        cls, manager: PQLManager, query_spec: str, queryset: Any
    ) -> Any:
        try:
            return manager.apply(query_spec=query_spec, queryset=queryset)
        except Exception as e:
            raise PQLException("Error applying or resolving queryset, %s" % e)

    @classmethod
    def parse_field(cls, field: str) -> Tuple[str, Optional[str]]:
        return parse_field(field=field)
