from django.db import IntegrityError
from django.core.cache import cache
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Profile, PlayerStats
from .serializers import (
    ProfileSerializer, ProfileUpdateSerializer,
    AvatarUpdateSerializer, PlayerStatsSerializer, PublicProfileSerializer,
)


def ensure_profile(player):
    """Get or create profile and stats for a player."""
    username = f'player_{str(player.id).replace("-","")[:12]}'
    profile, _ = Profile.objects.get_or_create(
        player=player,
        defaults={'username': username, 'display_name': username},
    )
    PlayerStats.objects.get_or_create(player=player)
    return profile


class MyProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = ensure_profile(request.user)
        return Response(ProfileSerializer(profile).data)

    def patch(self, request):
        profile = ensure_profile(request.user)
        ser = ProfileUpdateSerializer(profile, data=request.data, partial=True)
        if not ser.is_valid():
            return Response(ser.errors, status=400)
        try:
            ser.save()
            cache.delete(f'profile:{request.user.id}')
        except IntegrityError:
            return Response({'error': 'Username already taken'}, status=409)
        return Response(ProfileSerializer(profile).data)


class MyAvatarView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        profile = ensure_profile(request.user)
        ser = AvatarUpdateSerializer(profile, data=request.data, partial=True)
        if not ser.is_valid():
            return Response(ser.errors, status=400)
        ser.save()
        return Response(ProfileSerializer(profile).data)


class MyStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        stats, _ = PlayerStats.objects.get_or_create(player=request.user)
        return Response(PlayerStatsSerializer(stats).data)


class PublicProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, player_id):
        cache_key = f'profile:{player_id}'
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        try:
            profile = Profile.objects.select_related('player__stats').get(player_id=player_id)
        except Profile.DoesNotExist:
            return Response({'error': 'Player not found'}, status=404)

        data = PublicProfileSerializer(profile).data
        cache.set(cache_key, data, timeout=60)
        return Response(data)


class PlayerSearchView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class   = PublicProfileSerializer

    def get_queryset(self):
        q = self.request.query_params.get('q', '')
        if not q:
            return Profile.objects.none()
        return Profile.objects.filter(
            username__icontains=q
        ).select_related('player__stats').order_by('-level')[:50]
