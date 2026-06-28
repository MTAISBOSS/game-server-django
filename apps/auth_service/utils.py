import random
import bcrypt
import logging
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


def generate_otp() -> str:
    return str(random.randint(100000, 999999))


def hash_otp(otp: str) -> str:
    return bcrypt.hashpw(otp.encode(), bcrypt.gensalt()).decode()


def verify_otp(otp: str, hashed: str) -> bool:
    return bcrypt.checkpw(otp.encode(), hashed.encode())


def normalize_phone(phone: str, country_code: str = '1') -> str:
    digits = ''.join(c for c in phone if c.isdigit())
    if len(digits) < 7 or len(digits) > 15:
        return None
    if phone.startswith('+'):
        return phone
    return f'+{country_code}{digits}'


def mask_phone(phone: str) -> str:
    if len(phone) < 6:
        return '****'
    return phone[:3] + '****' + phone[-3:]


def send_otp(phone: str, otp: str) -> bool:
    if settings.SMS_PROVIDER == 'twilio':
        try:
            from twilio.rest import Client
            client = Client(settings.TWILIO_SID, settings.TWILIO_TOKEN)
            client.messages.create(
                body=f'Your game verification code: {otp}. Valid for {settings.OTP_EXPIRY_MINUTES} minutes.',
                from_=settings.TWILIO_FROM,
                to=phone,
            )
            return True
        except Exception as e:
            logger.error(f'Twilio send failed: {e}')
            return False
    else:
        # Dev mode — print to logs
        logger.warning(f'[DEV OTP] {mask_phone(phone)} → {otp}')
        return True


def otp_expiry():
    return timezone.now() + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
