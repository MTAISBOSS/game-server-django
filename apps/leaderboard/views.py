from django.core.cache import cache
from django.db import transaction
from django.db.models import Window, F
from django.db.models.functions import Rank
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Season, LeaderboardEntry, ScoreHistory
from .serializers import (
    SeasonSerializer, RankEntrySerializer,
    ScoreSubmitSerializer, ScoreResultSerializer,
)


def build_board(season, limit=50, offset=0):
    """Build leaderboard with ranks using window function."""
    entries = (
        LeaderboardEntry.objects
        .filter(season=season)
        .select_related('player__profile', 'player__stats')
        .order_by('-score')[offset:offset + limit]
    )

    result = []
    for i, entry in enumerate(entries, start=offset + 1):
        profile = getattr(entry.player, 'profile', None)
        result.append({
            'rank':         i,
            'player_id':    str(entry.player_id),
            'display_name': profile.display_name if profile else '',
            'avatar_id':    profile.avatar_id    if profile else 'default',
            'score':        entry.score,
            'level':        profile.level        if profile else 1,
            'country':      profile.country      if profile else '',
        })
    return result


class GlobalBoardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        page      = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('pageSize', 50)), 100)
        offset    = (page - 1) * page_size

        season = Season.get_active()
        if not season:
            return Response({'entries': [], 'total': 0, 'page': page})

        cache_key = f'lb:global:{season.id}:{page}:{page_size}'
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        entries = build_board(season, page_size, offset)
        total   = LeaderboardEntry.objects.filter(season=season).count()
        data    = {'entries': entries, 'total': total, 'page': page, 'season_id': str(season.id)}

        cache.set(cache_key, data, timeout=30)
        return Response(data)


class TopPlayersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count     = min(int(request.query_params.get('count', 10)), 100)
        season_id = request.query_params.get('seasonId')

        season = Season.objects.get(id=season_id) if season_id else Season.get_active()
        if not season:
            return Response({'entries': [], 'total': 0})

        cache_key = f'lb:top:{season.id}:{count}'
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        entries = build_board(season, count, 0)
        data    = {'entries': entries, 'total': len(entries), 'season_id': str(season.id)}
        cache.set(cache_key, data, timeout=30)
        return Response(data)


class MyRankView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        season_id = request.query_params.get('seasonId')
        season    = Season.objects.get(id=season_id) if season_id else Season.get_active()
        if not season:
            return Response({'rank': 0, 'score': 0, 'player_id': str(request.user.id)})

        try:
            entry = LeaderboardEntry.objects.get(player=request.user, season=season)
        except LeaderboardEntry.DoesNotExist:
            return Response({'rank': 0, 'score': 0, 'player_id': str(request.user.id)})

        rank = LeaderboardEntry.objects.filter(season=season, score__gt=entry.score).count() + 1
        return Response({'rank': rank, 'score': entry.score, 'player_id': str(request.user.id)})


class SubmitScoreView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = ScoreSubmitSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=400)

        season = Season.get_active()
        if not season:
            return Response({'error': 'No active season'}, status=404)

        score    = ser.validated_data['score']
        match_id = ser.validated_data['match_id']
        metadata = ser.validated_data['metadata']

        with transaction.atomic():
            entry, _ = LeaderboardEntry.objects.select_for_update().get_or_create(
                player=request.user, season=season, defaults={'score': 0}
            )
            prev_score = entry.score
            new_score  = max(prev_score + score, 0)
            is_high    = new_score > prev_score

            entry.score = new_score
            entry.save(update_fields=['score', 'updated_at'])

            ScoreHistory.objects.create(
                player=request.user, season=season,
                match_id=match_id, delta=score,
                score_after=new_score, metadata=metadata,
            )

        new_rank = LeaderboardEntry.objects.filter(season=season, score__gt=new_score).count() + 1

        # Bust cache
        cache.delete_pattern(f'lb:global:{season.id}:*')
        cache.delete_pattern(f'lb:top:{season.id}:*')

        return Response({
            'new_score':     new_score,
            'rank':          new_rank,
            'previous_rank': 0,
            'is_highscore':  is_high,
        })


class FriendsBoardView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        friend_ids = request.data.get('friend_ids', [])[:100]
        all_ids    = list(set([str(request.user.id)] + friend_ids))

        season = Season.get_active()
        if not season:
            return Response({'entries': [], 'total': 0})

        entries = (
            LeaderboardEntry.objects
            .filter(season=season, player_id__in=all_ids)
            .select_related('player__profile')
            .order_by('-score')
        )

        result = []
        for i, e in enumerate(entries, start=1):
            profile = getattr(e.player, 'profile', None)
            result.append({
                'rank':         i,
                'player_id':    str(e.player_id),
                'display_name': profile.display_name if profile else '',
                'avatar_id':    profile.avatar_id    if profile else 'default',
                'score':        e.score,
                'level':        profile.level        if profile else 1,
                'country':      profile.country      if profile else '',
            })

        return Response({'entries': result, 'total': len(result), 'season_id': str(season.id)})


class SeasonListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        seasons = Season.objects.all()
        return Response({'seasons': SeasonSerializer(seasons, many=True).data})


class CurrentSeasonView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        season = Season.get_active()
        if not season:
            return Response({'error': 'No active season'}, status=404)
        return Response(SeasonSerializer(season).data)


class SeasonBoardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, season_id):
        page      = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('pageSize', 50)), 100)
        offset    = (page - 1) * page_size

        try:
            season = Season.objects.get(id=season_id)
        except Season.DoesNotExist:
            return Response({'error': 'Season not found'}, status=404)

        entries = build_board(season, page_size, offset)
        total   = LeaderboardEntry.objects.filter(season=season).count()
        return Response({'entries': entries, 'total': total, 'page': page, 'season_id': str(season_id)})
