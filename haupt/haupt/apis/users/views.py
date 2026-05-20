from rest_framework import status
from rest_framework.response import Response

from haupt.apis.endpoints.user_ssh_keys import (
    UserSshKeyDetailEndpoint,
    UserSshKeyListEndpoint,
    get_ssh_key_user,
)
from haupt.apis.serializers.user_ssh_keys import (
    UserSshKeyCreateResponseSerializer,
)
from haupt.db.abstracts.user_ssh_keys import UserSshKeyConflict
from haupt.db.defs import Models


class UserSshKeyListCreateView(UserSshKeyListEndpoint):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = get_ssh_key_user(request)
        public_key = serializer.validated_data["public_key"]
        name = serializer.validated_data.get("name")
        try:
            self.check_key_cap(user=user, public_key=public_key)
            key, created = Models.UserSshKey.objects.register(
                user=user,
                public_key=public_key,
                name=name,
            )
        except UserSshKeyConflict as e:
            return Response(
                status=status.HTTP_409_CONFLICT,
                data={"detail": str(e)},
            )
        except ValueError as e:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"detail": str(e)},
            )

        return Response(
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
            data=UserSshKeyCreateResponseSerializer(key).data,
        )


class UserSshKeyDetailView(UserSshKeyDetailEndpoint):
    def perform_destroy(self, instance):
        Models.UserSshKey.objects.revoke(
            user=get_ssh_key_user(self.request),
            key_uuid=instance.uuid,
        )
