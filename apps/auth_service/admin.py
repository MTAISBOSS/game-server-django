from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Player, OTPCode, RefreshTokenRecord


@admin.register(Player)
class PlayerAdmin(UserAdmin):
    list_display  = ['id', 'device_id', 'phone', 'role', 'is_banned', 'platform', 'created_at']
    list_filter   = ['role', 'is_banned', 'platform']
    search_fields = ['device_id', 'phone', 'id']
    ordering      = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_login']
    fieldsets = (
        ('Identity',    {'fields': ('id', 'device_id', 'phone', 'country_code')}),
        ('Status',      {'fields': ('role', 'is_banned', 'ban_reason', 'is_active')}),
        ('Device Info', {'fields': ('platform', 'app_version')}),
        ('Timestamps',  {'fields': ('created_at', 'updated_at', 'last_login')}),
    )
    add_fieldsets = (
        (None, {'fields': ('device_id', 'phone', 'role')}),
    )

    actions = ['ban_players', 'unban_players']

    def ban_players(self, request, queryset):
        queryset.update(is_banned=True)
    ban_players.short_description = 'Ban selected players'

    def unban_players(self, request, queryset):
        queryset.update(is_banned=False)
    unban_players.short_description = 'Unban selected players'


@admin.register(OTPCode)
class OTPAdmin(admin.ModelAdmin):
    list_display = ['phone', 'player', 'attempts', 'expires_at', 'verified_at', 'created_at']
    list_filter  = ['verified_at']
    readonly_fields = ['code_hash']


@admin.register(RefreshTokenRecord)
class RefreshTokenAdmin(admin.ModelAdmin):
    list_display = ['player', 'device_id', 'expires_at', 'revoked_at', 'created_at']
