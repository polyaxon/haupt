from rest_framework import status
from rest_framework.response import Response

from haupt.common.endpoints.base import BaseEndpoint, PostEndpoint, RetrieveEndpoint
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
        trigger_cron()
        return Response(status=status.HTTP_200_OK)
