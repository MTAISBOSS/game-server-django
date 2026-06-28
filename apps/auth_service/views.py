import logging
from django.utils import timezone
from django.db import transaction
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .models import Player, OTPCode, RefreshTokenRecord
from .serializers import (
    DeviceAuthSerializer, PhoneLinkSerializer, OTPVerifySerializer,
    PhoneLoginSerializer, RefreshSerializer,
)
from .utils import (
    generate_otp, hash_otp, verify_otp,
    normalize_phone, send_otp, otp_expiry,
)
from django.conf import settings

logger = logging.getLogger(__name__)


def make_token_response(player, is_new=False):
    refresh = RefreshToken.for_user(player)
    refresh['player_id'] = str(player.id)
    refresh['device_id'] = player.device_id or ''
    refresh['phone']     = player.phone or ''
    refresh['role']      = player.role
    access = refresh.access_token

    return {
        'access_token':  str(access),
        'refresh_token': str(refresh),
        'player_id':     str(player.id),
        'is_new_player': is_new,
        'expires_at':    int(access['exp']),
    }


class DeviceAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = DeviceAuthSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=400)

        device_id   = ser.validated_data['device_id'].strip()
        platform    = ser.validated_data['platform']
        app_version = ser.validated_data['app_version']

        player, created = Player.objects.get_or_create(
            device_id=device_id,
            defaults={'platform': platform, 'app_version': app_version},
        )

        if not created:
            player.app_version = app_version
            player.save(update_fields=['app_version', 'updated_at'])

        if player.is_banned:
            return Response({'error': 'Account suspended'}, status=403)

        logger.info(f'Device auth: {device_id[:8]}*** new={created}')
        return Response(make_token_response(player, is_new=created))


class PhoneLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = PhoneLinkSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=400)

        phone = normalize_phone(
            ser.validated_data['phone_number'],
            ser.validated_data['country_code'],
        )
        if not phone:
            return Response({'error': 'Invalid phone number'}, status=400)

        # Check not used by another account
        if Player.objects.filter(phone=phone).exclude(id=request.user.id).exists():
            return Response({'error': 'Phone already linked to another account'}, status=409)

        # Invalidate old OTPs
        OTPCode.objects.filter(phone=phone, verified_at__isnull=True).delete()

        otp  = generate_otp()
        code = OTPCode.objects.create(
            player=request.user,
            phone=phone,
            code_hash=hash_otp(otp),
            expires_at=otp_expiry(),
        )

        if not send_otp(phone, otp):
            return Response({'error': 'Failed to send OTP'}, status=500)

        return Response({'message': 'OTP sent', 'player_id': str(request.user.id)})


class OTPVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = OTPVerifySerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=400)

        phone = normalize_phone(
            ser.validated_data['phone_number'],
            ser.validated_data['country_code'],
        )
        otp = ser.validated_data['otp']

        record = OTPCode.objects.filter(
            phone=phone,
            player=request.user,
            verified_at__isnull=True,
        ).order_by('-created_at').first()

        if not record:
            return Response({'error': 'No pending OTP'}, status=404)
        if record.is_expired:
            return Response({'error': 'OTP expired'}, status=408)
        if record.attempts >= settings.OTP_MAX_ATTEMPTS:
            return Response({'error': 'Too many attempts'}, status=429)
        if not verify_otp(otp, record.code_hash):
            record.attempts += 1
            record.save(update_fields=['attempts'])
            return Response({'error': 'Invalid OTP'}, status=400)

        with transaction.atomic():
            record.verified_at = timezone.now()
            record.save(update_fields=['verified_at'])
            request.user.phone        = phone
            request.user.country_code = ser.validated_data['country_code']
            request.user.save(update_fields=['phone', 'country_code', 'updated_at'])

        return Response(make_token_response(request.user))


class PhoneLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = PhoneLoginSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=400)

        phone = normalize_phone(
            ser.validated_data['phone_number'],
            ser.validated_data['country_code'],
        )

        try:
            player = Player.objects.get(phone=phone)
        except Player.DoesNotExist:
            return Response({'error': 'No account with this phone number'}, status=404)

        OTPCode.objects.filter(phone=phone, verified_at__isnull=True).delete()

        otp = generate_otp()
        OTPCode.objects.create(
            player=player,
            phone=phone,
            code_hash=hash_otp(otp),
            expires_at=otp_expiry(),
        )

        send_otp(phone, otp)
        return Response({'message': 'OTP sent', 'player_id': str(player.id)})


class PhoneLoginVerifyView(APIView):
    """Verify OTP for phone-only login (no existing session needed)."""
    permission_classes = [AllowAny]

    def post(self, request):
        ser = OTPVerifySerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=400)

        phone = normalize_phone(
            ser.validated_data['phone_number'],
            ser.validated_data['country_code'],
        )

        try:
            player = Player.objects.get(phone=phone)
        except Player.DoesNotExist:
            return Response({'error': 'Account not found'}, status=404)

        record = OTPCode.objects.filter(
            phone=phone, player=player, verified_at__isnull=True,
        ).order_by('-created_at').first()

        if not record:
            return Response({'error': 'No pending OTP'}, status=404)
        if record.is_expired:
            return Response({'error': 'OTP expired'}, status=408)
        if record.attempts >= settings.OTP_MAX_ATTEMPTS:
            return Response({'error': 'Too many attempts'}, status=429)
        if not verify_otp(ser.validated_data['otp'], record.code_hash):
            record.attempts += 1
            record.save(update_fields=['attempts'])
            return Response({'error': 'Invalid OTP'}, status=400)

        record.verified_at = timezone.now()
        record.save(update_fields=['verified_at'])

        if player.is_banned:
            return Response({'error': 'Account suspended'}, status=403)

        return Response(make_token_response(player))


class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = RefreshSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=400)

        try:
            old_refresh = RefreshToken(ser.validated_data['refresh_token'])
            old_refresh.blacklist()
            player = Player.objects.get(id=old_refresh['player_id'])
            return Response(make_token_response(player))
        except (TokenError, Player.DoesNotExist) as e:
            return Response({'error': 'Invalid or expired refresh token'}, status=401)


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = RefreshSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=400)

        try:
            token = RefreshToken(ser.validated_data['refresh_token'])
            token.blacklist()
        except TokenError:
            pass

        return Response({'message': 'Logged out successfully'})


class HealthView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'status': 'ok', 'service': 'game-backend-django'})
