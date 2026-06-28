from rest_framework import serializers
from .models import Player


class DeviceAuthSerializer(serializers.Serializer):
    device_id   = serializers.CharField(min_length=8, max_length=256)
    platform    = serializers.CharField(default='unknown', required=False)
    app_version = serializers.CharField(default='1.0.0', required=False)


class PhoneLinkSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    country_code = serializers.CharField(max_length=5, default='1', required=False)


class OTPVerifySerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    country_code = serializers.CharField(max_length=5, default='1', required=False)
    otp          = serializers.CharField(min_length=6, max_length=6)


class PhoneLoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    country_code = serializers.CharField(max_length=5, default='1', required=False)


class RefreshSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Player
        fields = ['id', 'device_id', 'phone', 'role', 'is_banned',
                  'platform', 'app_version', 'created_at', 'phone_linked']
        read_only_fields = fields
