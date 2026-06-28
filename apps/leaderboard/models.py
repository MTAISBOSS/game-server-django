import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class Season(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name       = models.CharField(max_length=100)
    starts_at  = models.DateTimeField()
    ends_at    = models.DateTimeField()
    is_active  = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'seasons'
        ordering = ['-starts_at']

    def __str__(self):
        return f'{self.name} ({"active" if self.is_active else "inactive"})'

    def save(self, *args, **kwargs):
        # Only one active season at a time
        if self.is_active:
            Season.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_active(cls):
        return cls.objects.filter(is_active=True).first()


class LeaderboardEntry(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player     = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='leaderboard_entries'
    )
    season     = models.ForeignKey(Season, on_delete=models.CASCADE, related_name='entries')
    score      = models.BigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table    = 'leaderboard_entries'
        unique_together = [['player', 'season']]
        indexes = [
            models.Index(fields=['season', '-score']),
            models.Index(fields=['player']),
        ]

    def __str__(self):
        return f'{self.player} — {self.score}'


class ScoreHistory(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player      = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='score_history'
    )
    season      = models.ForeignKey(Season, on_delete=models.CASCADE)
    match_id    = models.CharField(max_length=100, blank=True, default='')
    delta       = models.BigIntegerField()
    score_after = models.BigIntegerField()
    metadata    = models.JSONField(default=dict, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'score_history'
        indexes  = [models.Index(fields=['player', 'season', '-created_at'])]
