import uuid
import hashlib
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


class PlayerManager(BaseUserManager):
    def create_user(self, device_id=None, phone=None, **extra):
        if not device_id and not phone:
            raise ValueError('Player must have device_id or phone')
        player = self.model(device_id=device_id, phone=phone, **extra)
        player.set_unusable_password()
        player.save(using=self._db)
        return player

    def create_superuser(self, username, password, **extra):
        player = self.model(username=username, role='admin', is_staff=True, is_superuser=True, **extra)
        player.set_password(password)
        player.save(using=self._db)
        return player


class Player(AbstractBaseUser, PermissionsMixin):
    ROLES = [('player', 'Player'), ('admin', 'Admin'), ('moderator', 'Moderator')]

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device_id    = models.TextField(unique=True, null=True, blank=True)
    phone        = models.CharField(max_length=20, unique=True, null=True, blank=True)
    country_code = models.CharField(max_length=5, blank=True, default='')
    platform     = models.CharField(max_length=20, blank=True, default='unknown')
    app_version  = models.CharField(max_length=20, blank=True, default='1.0.0')
    role         = models.CharField(max_length=20, choices=ROLES, default='player')
    is_banned    = models.BooleanField(default=False)
    ban_reason   = models.TextField(blank=True, default='')
    is_active    = models.BooleanField(default=True)
    is_staff     = models.BooleanField(default=False)
    username     = models.CharField(max_length=150, blank=True, default='')
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)
    last_login   = models.DateTimeField(null=True, blank=True)

    objects = PlayerManager()

    USERNAME_FIELD  = 'id'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'players'
        indexes  = [
            models.Index(fields=['device_id']),
            models.Index(fields=['phone']),
            models.Index(fields=['role']),
            models.Index(fields=['is_banned']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.device_id or self.phone or str(self.id)}"

    @property
    def phone_linked(self):
        return bool(self.phone)


class RefreshTokenRecord(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player     = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='refresh_tokens')
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    device_id  = models.TextField(blank=True, default='')
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'refresh_tokens'

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    @property
    def is_valid(self):
        return self.revoked_at is None and self.expires_at > timezone.now()


class OTPCode(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player      = models.ForeignKey(Player, on_delete=models.CASCADE, null=True, blank=True)
    phone       = models.CharField(max_length=20, db_index=True)
    code_hash   = models.CharField(max_length=128)
    attempts    = models.IntegerField(default=0)
    expires_at  = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'otp_codes'

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_verified(self):
        return self.verified_at is not None
