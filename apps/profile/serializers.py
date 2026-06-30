import re
from rest_framework import serializers
from .models import Profile, PlayerStats


class ProfileSerializer(serializers.ModelSerializer):
    phone_linked = serializers.SerializerMethodField()

    class Meta:
        model  = Profile
        fields = ['player_id', 'username', 'display_name', 'bio',
                  'avatar_id', 'frame_id', 'country', 'level', 'xp',
                  'phone_linked', 'created_at']
        read_only_fields = ['player_id', 'level', 'xp', 'created_at', 'phone_linked']

    def get_phone_linked(self, obj):
        return bool(obj.player.phone)

    def validate_username(self, value):
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', value):
            raise serializers.ValidationError(
                'Username must be 3-20 alphanumeric characters or underscores'
            )
        return value


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Profile
        fields = ['username', 'display_name', 'bio', 'country']

    def validate_username(self, value):
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', value):
            raise serializers.ValidationError('Invalid username format')
        return value


class AvatarUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Profile
        fields = ['avatar_id', 'frame_id']


class PlayerStatsSerializer(serializers.ModelSerializer):
    win_rate  = serializers.FloatField(read_only=True)
    class Meta:
        model  = PlayerStats
        fields = ['player_id', 'games_played', 'wins', 'losses',
                  'win_streak', 'best_streak', 'win_rate', 'total_xp', 'total_score']


class PublicProfileSerializer(serializers.ModelSerializer):
    stats = PlayerStatsSerializer(source='player.stats', read_only=True)

    class Meta:
        model  = Profile
        fields = ['player_id', 'username', 'display_name', 'avatar_id',
                  'frame_id', 'country', 'level', 'stats']
