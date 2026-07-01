"""
Shared serializer classes used only for OpenAPI schema generation.
Defined once here (not inline) to avoid drf-spectacular name collisions.
"""
from rest_framework import serializers


class ErrorResponseSerializer(serializers.Serializer):
    """Generic error response: { "error": "..." }"""
    error = serializers.CharField()


class MessageResponseSerializer(serializers.Serializer):
    """Generic message response: { "message": "..." }"""
    message = serializers.CharField()


class OtpSentResponseSerializer(serializers.Serializer):
    """Response when an OTP is sent to a phone number."""
    message   = serializers.CharField(default='OTP sent')
    player_id = serializers.UUIDField()


class TokenResponseSerializer(serializers.Serializer):
    """JWT token pair returned after authentication."""
    access_token  = serializers.CharField()
    refresh_token = serializers.CharField()
    player_id     = serializers.UUIDField()
    is_new_player = serializers.BooleanField()
    expires_at    = serializers.IntegerField()


class HealthResponseSerializer(serializers.Serializer):
    """Service health check response."""
    status  = serializers.CharField()
    service = serializers.CharField()
