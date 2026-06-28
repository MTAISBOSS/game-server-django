from rest_framework import serializers
from .models import Season, LeaderboardEntry, ScoreHistory


class SeasonSerializer(serializers.ModelSerializer):
    season_id = serializers.UUIDField(source='id', read_only=True)

    class Meta:
        model  = Season
        fields = ['season_id', 'name', 'starts_at', 'ends_at', 'is_active']


class SeasonCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Season
        fields = ['name', 'starts_at', 'ends_at', 'is_active']


class RankEntrySerializer(serializers.Serializer):
    rank         = serializers.IntegerField()
    player_id    = serializers.UUIDField()
    display_name = serializers.CharField()
    avatar_id    = serializers.CharField()
    score        = serializers.IntegerField()
    level        = serializers.IntegerField()
    country      = serializers.CharField()


class ScoreSubmitSerializer(serializers.Serializer):
    score    = serializers.IntegerField()
    match_id = serializers.CharField(required=False, default='', allow_blank=True)
    metadata = serializers.DictField(required=False, default=dict)


class ScoreResultSerializer(serializers.Serializer):
    new_score     = serializers.IntegerField()
    rank          = serializers.IntegerField()
    previous_rank = serializers.IntegerField()
    is_highscore  = serializers.BooleanField()
