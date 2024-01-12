from clipped.utils.bools import to_bool
from rest_framework import status
from rest_framework.response import Response

from django.http import HttpRequest

from haupt.apis.serializers.runs import RunDetailSerializer
from haupt.common.apis.regex import OWNER_NAME_KEY, RUN_UUID_KEY, UUID_KEY
from haupt.common.endpoints.base import BaseEndpoint, PostEndpoint, RetrieveEndpoint
from haupt.db.defs import Models
from haupt.db.managers.agents import get_agent_state, trigger_cron
from polyaxon.schemas import LiveState, V1Statuses


class AgentStateViewV1(BaseEndpoint, RetrieveEndpoint):
    ALLOWED_METHODS = ["GET"]

    def get(self, request, *args, **kwargs):
        state = get_agent_state()
        return Response(
            data={
                "state": state,
                "status": V1Statuses.RUNNING,
                "live_state": LiveState.LIVE,
            },
            status=status.HTTP_200_OK,
        )


class AgentCronViewV1(BaseEndpoint, PostEndpoint):
    ALLOWED_METHODS = ["POST"]

    def post(self, request, *args, **kwargs):
        _state = to_bool(request.data.get("state", False), handle_none=True)
        state = trigger_cron(state=_state)
        return Response(
            data={
                "state": state,
                "status": V1Statuses.RUNNING,
                "live_state": LiveState.LIVE,
            },
            status=status.HTTP_200_OK,
        )


class AgentRunDetailView(BaseEndpoint, RetrieveEndpoint):
    serializer_class = RunDetailSerializer
    queryset = Models.Run.all.select_related(
        "original",
        "pipeline",
        "project",
    ).prefetch_related("contributors")
    ALLOWED_METHODS = ["GET"]
    lookup_field = UUID_KEY
    lookup_url_kwarg = RUN_UUID_KEY
    CONTEXT_KEYS = (OWNER_NAME_KEY, RUN_UUID_KEY)
    CONTEXT_OBJECTS = ("run",)

    def initialize_object_context(self, request: HttpRequest, *args, **kwargs) -> None:
        #  pylint:disable=attribute-defined-outside-init
        self.run = self.get_object()
