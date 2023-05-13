from haupt.common.query.service import QueryService
from haupt.common.service_interface import LazyServiceWrapper

backend = LazyServiceWrapper(
    backend_base=QueryService,
    backend_path="haupt.common.query.service.QueryService",
    options={},
)
backend.expose(locals())
