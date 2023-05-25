from rest_framework import status
from rest_framework.response import Response

from haupt.common.endpoints.base import BaseEndpoint, RetrieveEndpoint
from haupt.db.managers.agents import get_agent_state


class AgentStateViewV1(BaseEndpoint, RetrieveEndpoint):
    ALLOWED_METHODS = ["GET"]

    def get(self, request, *args, **kwargs):
        state = get_agent_state()

        return Response(
            data={"state": state},
            status=status.HTTP_200_OK,
        )
