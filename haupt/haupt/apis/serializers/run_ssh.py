from rest_framework import serializers


class RunSshAccessValidateSerializer(serializers.Serializer):
    fingerprint = serializers.RegexField(regex=r"^SHA256:[A-Za-z0-9+/]{43}$")
