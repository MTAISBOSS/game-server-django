import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from datetime import timedelta


class StatsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']
        if not user.is_authenticated or not (user.is_staff or user.role == 'admin'):
            await self.close()
            return
        await self.channel_layer.group_add('stats', self.channel_name)
        await self.accept()
        # Send initial data on connect
        stats = await self.get_stats()
        await self.send(text_data=json.dumps(stats))

    async def disconnect(self, code):
        await self.channel_layer.group_discard('stats', self.channel_name)

    async def stats_update(self, event):
        await self.send(text_data=json.dumps(event['data']))

    @database_sync_to_async
    def get_stats(self):
        from apps.auth_service.models import Player
        from apps.resources.models import Transaction
        from apps.leaderboard.models import Season
        now = timezone.now()
        day = now - timedelta(days=1)
        return {
            'type':           'stats',
            'total_players':  Player.objects.count(),
            'new_today':      Player.objects.filter(created_at__gte=day).count(),
            'banned':         Player.objects.filter(is_banned=True).count(),
            'tx_today':       Transaction.objects.filter(created_at__gte=day).count(),
            'active_season':  str(Season.get_active()) if Season.get_active() else 'None',
            'ts':             now.isoformat(),
        }
