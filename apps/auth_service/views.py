import logging
from django.utils import timezone
from django.db import transaction
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from drf_spectacular.utils import extend_schema

from .models import Player, OTPCode, RefreshTokenRecord
from .serializers import (
    DeviceAuthSerializer, PhoneLinkSerializer, OTPVerifySerializer,
    PhoneLoginSerializer, RefreshSerializer,
)
from .schema_serializers import (
    TokenResponseSerializer, OtpSentResponseSerializer,
    ErrorResponseSerializer, MessageResponseSerializer, HealthResponseSerializer,
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

    @extend_schema(
        operation_id='auth_device',
        summary='Device login / register',
        description='Authenticate or register a new player via device ID. '
                    'Returns JWT access + refresh tokens.',
        request=DeviceAuthSerializer,
        responses={200: TokenResponseSerializer, 400: ErrorResponseSerializer, 403: ErrorResponseSerializer},
        tags=['Auth'],
    )
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

    @extend_schema(
        operation_id='auth_phone_link',
        summary='Link phone number',
        description='Request an OTP to link a phone number to the current account. '
                    'Requires JWT authentication.',
        request=PhoneLinkSerializer,
        responses={
            200: OtpSentResponseSerializer,
            400: ErrorResponseSerializer,
            409: ErrorResponseSerializer,
            500: ErrorResponseSerializer,
        },
        tags=['Auth'],
    )
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

    @extend_schema(
        operation_id='auth_phone_verify',
        summary='Verify OTP (phone link)',
        description='Verify the OTP sent during phone linking. '
                    'On success, the phone is permanently linked and a new token pair is issued.',
        request=OTPVerifySerializer,
        responses={
            200: TokenResponseSerializer,
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
            408: ErrorResponseSerializer,
            429: ErrorResponseSerializer,
        },
        tags=['Auth'],
    )
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

    @extend_schema(
        operation_id='auth_phone_login',
        summary='Phone login (request OTP)',
        description='Request an OTP for phone-based login. '
                    'No existing session required. The phone must already be linked to an account.',
        request=PhoneLoginSerializer,
        responses={200: OtpSentResponseSerializer, 400: ErrorResponseSerializer, 404: ErrorResponseSerializer},
        tags=['Auth'],
    )
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

    @extend_schema(
        operation_id='auth_phone_confirm',
        summary='Phone login confirm (verify OTP)',
        description='Verify the OTP and complete phone-based login. '
                    'No existing session required. Returns JWT tokens on success.',
        request=OTPVerifySerializer,
        responses={
            200: TokenResponseSerializer,
            400: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
            408: ErrorResponseSerializer,
            429: ErrorResponseSerializer,
        },
        tags=['Auth'],
    )
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

    @extend_schema(
        operation_id='auth_refresh',
        summary='Refresh access token',
        description='Exchange a valid refresh token for a new JWT token pair. '
                    'The old refresh token is immediately blacklisted.',
        request=RefreshSerializer,
        responses={200: TokenResponseSerializer, 400: ErrorResponseSerializer, 401: ErrorResponseSerializer},
        tags=['Auth'],
    )
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

    @extend_schema(
        operation_id='auth_logout',
        summary='Logout',
        description='Blacklist the refresh token to end the session.',
        request=RefreshSerializer,
        responses={200: MessageResponseSerializer, 400: ErrorResponseSerializer},
        tags=['Auth'],
    )
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

    @extend_schema(
        operation_id='health_check',
        summary='Health check',
        description='Returns service health status.',
        responses={200: HealthResponseSerializer},
        tags=['System'],
    )
    def get(self, request):
        return Response({'status': 'ok', 'service': 'game-backend-django'})
