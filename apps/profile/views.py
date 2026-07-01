from django.db import IntegrityError
from django.core.cache import cache
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.auth_service.schema_serializers import ErrorResponseSerializer
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

    @extend_schema(
        operation_id='profile_me_get',
        summary='Get my profile',
        description='Get the current player\'s full profile. Auto-creates a profile if none exists.',
        responses={200: ProfileSerializer},
        tags=['Profile'],
    )
    def get(self, request):
        profile = ensure_profile(request.user)
        return Response(ProfileSerializer(profile).data)

    @extend_schema(
        operation_id='profile_me_patch',
        summary='Update my profile',
        description='Partially update profile fields (username, display_name, bio, country).',
        request=ProfileUpdateSerializer,
        responses={200: ProfileSerializer, 400: ErrorResponseSerializer, 409: ErrorResponseSerializer},
        tags=['Profile'],
    )
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

    @extend_schema(
        operation_id='profile_avatar_patch',
        summary='Update avatar',
        description='Update avatar_id and/or frame_id.',
        request=AvatarUpdateSerializer,
        responses={200: ProfileSerializer, 400: ErrorResponseSerializer},
        tags=['Profile'],
    )
    def patch(self, request):
        profile = ensure_profile(request.user)
        ser = AvatarUpdateSerializer(profile, data=request.data, partial=True)
        if not ser.is_valid():
            return Response(ser.errors, status=400)
        ser.save()
        return Response(ProfileSerializer(profile).data)


class MyStatsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id='profile_stats',
        summary='Get my stats',
        description='Get the current player\'s game statistics '
                    '(games played, wins, losses, win streak, etc.).',
        responses={200: PlayerStatsSerializer},
        tags=['Profile'],
    )
    def get(self, request):
        stats, _ = PlayerStats.objects.get_or_create(player=request.user)
        return Response(PlayerStatsSerializer(stats).data)


class PublicProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id='profile_public',
        summary='Get public profile',
        description='Get a public profile by player ID. '
                    'Includes username, display name, avatar, level, and stats.',
        responses={200: PublicProfileSerializer, 404: ErrorResponseSerializer},
        tags=['Profile'],
    )
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
    queryset           = Profile.objects.none()  # prevents AnonymousUser error in schema gen

    @extend_schema(
        operation_id='profile_search',
        summary='Search players',
        description='Search for players by username. Returns up to 50 results sorted by level (descending).',
        parameters=[
            OpenApiParameter('q', str, OpenApiParameter.QUERY,
                             description='Search query (username substring)', required=True),
        ],
        responses={200: PublicProfileSerializer(many=True)},
        tags=['Profile'],
    )
    def get_queryset(self):
        q = self.request.query_params.get('q', '')
        if not q:
            return Profile.objects.none()
        return Profile.objects.filter(
            username__icontains=q
        ).select_related('player__stats').order_by('-level')[:50]
