from django.contrib import admin
from .models import Profile, PlayerStats


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display  = ['username', 'display_name', 'country', 'level', 'xp', 'created_at']
    list_filter   = ['country', 'level']
    search_fields = ['username', 'display_name', 'player__id']
    readonly_fields = ['player', 'level', 'created_at', 'updated_at']
    ordering = ['-level', '-xp']


@admin.register(PlayerStats)
class PlayerStatsAdmin(admin.ModelAdmin):
    list_display  = ['player', 'games_played', 'wins', 'losses', 'win_streak', 'best_streak']
    readonly_fields = ['player']
