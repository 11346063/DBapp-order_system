from rest_framework import serializers

from web_app.utils.timezone import normalize_timezone


class TimezonePreferenceSerializer(serializers.Serializer):
    timezone = serializers.CharField(max_length=64)

    def validate_timezone(self, value):
        try:
            return normalize_timezone(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc))
