import uuid
from django.db import models
from django.conf import settings


class Profile(models.Model):
    player      = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        primary_key=True, related_name='profile'
    )
    username     = models.CharField(max_length=30, unique=True)
    display_name = models.CharField(max_length=60, blank=True, default='')
    bio          = models.TextField(blank=True, default='')
    avatar_id    = models.CharField(max_length=50, default='default')
    frame_id     = models.CharField(max_length=50, default='default')
    country      = models.CharField(max_length=3, blank=True, default='')
    level        = models.IntegerField(default=1)
    xp           = models.BigIntegerField(default=0)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'profiles'
        indexes  = [
            models.Index(fields=['username']),
            models.Index(fields=['country']),
            models.Index(fields=['level']),
        ]

    def __str__(self):
        return self.username

    def calc_level(self):
        import math
        return max(1, int(1 + math.sqrt(self.xp / 1000)))

    def save(self, *args, **kwargs):
        self.level = self.calc_level()
        super().save(*args, **kwargs)


class PlayerStats(models.Model):
    player       = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        primary_key=True, related_name='stats'
    )
    games_played = models.IntegerField(default=0)
    wins         = models.IntegerField(default=0)
    losses       = models.IntegerField(default=0)
    win_streak   = models.IntegerField(default=0)
    best_streak  = models.IntegerField(default=0)
    total_xp     = models.BigIntegerField(default=0)
    total_score  = models.BigIntegerField(default=0)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'player_stats'

    @property
    def win_rate(self):
        if self.games_played == 0:
            return 0.0
        return round((self.wins / self.games_played) * 100, 2)
