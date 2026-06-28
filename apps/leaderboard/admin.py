from django.contrib import admin
from .models import Season, LeaderboardEntry, ScoreHistory


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display  = ['name', 'starts_at', 'ends_at', 'is_active', 'created_at']
    list_filter   = ['is_active']
    ordering      = ['-starts_at']
    actions       = ['activate_season']

    def activate_season(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, 'Select exactly one season to activate.', level='error')
            return
        season = queryset.first()
        Season.objects.all().update(is_active=False)
        season.is_active = True
        season.save()
        self.message_user(request, f'Season "{season.name}" is now active.')
    activate_season.short_description = 'Set as active season'


@admin.register(LeaderboardEntry)
class LeaderboardEntryAdmin(admin.ModelAdmin):
    list_display  = ['player', 'season', 'score', 'updated_at']
    list_filter   = ['season']
    search_fields = ['player__id']
    ordering      = ['-score']
    readonly_fields = ['player', 'season']


@admin.register(ScoreHistory)
class ScoreHistoryAdmin(admin.ModelAdmin):
    list_display  = ['player', 'season', 'delta', 'score_after', 'match_id', 'created_at']
    list_filter   = ['season']
    readonly_fields = ['player', 'season', 'created_at']
