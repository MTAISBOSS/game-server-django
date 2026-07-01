"""
Shared serializer classes used only for OpenAPI schema generation.
Defined once here (not inline) to avoid drf-spectacular name collisions.
"""
from rest_framework import serializers
from .serializers import RankEntrySerializer, SeasonSerializer


class GlobalBoardResponseSerializer(serializers.Serializer):
    """Paginated global leaderboard response."""
    entries   = RankEntrySerializer(many=True)
    total     = serializers.IntegerField()
    page      = serializers.IntegerField()
    season_id = serializers.UUIDField()


class TopPlayersResponseSerializer(serializers.Serializer):
    """Top players response (no pagination)."""
    entries   = RankEntrySerializer(many=True)
    total     = serializers.IntegerField()
    season_id = serializers.UUIDField()


class MyRankResponseSerializer(serializers.Serializer):
    """Current player's rank response."""
    rank      = serializers.IntegerField()
    score     = serializers.IntegerField()
    player_id = serializers.UUIDField()


class FriendsBoardResponseSerializer(serializers.Serializer):
    """Friends leaderboard response."""
    entries   = RankEntrySerializer(many=True)
    total     = serializers.IntegerField()
    season_id = serializers.UUIDField()


class SeasonListResponseSerializer(serializers.Serializer):
    """List of all seasons."""
    seasons = SeasonSerializer(many=True)


class SeasonBoardResponseSerializer(serializers.Serializer):
    """Paginated season leaderboard response."""
    entries   = RankEntrySerializer(many=True)
    total     = serializers.IntegerField()
    page      = serializers.IntegerField()
    season_id = serializers.UUIDField()


class FriendsBoardRequestSerializer(serializers.Serializer):
    """Request body for friends leaderboard."""
    friend_ids = serializers.ListField(
        child=serializers.UUIDField(),
        help_text='List of friend player UUIDs',
    )
