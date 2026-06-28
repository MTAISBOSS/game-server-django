from django.contrib import admin
from django.db import transaction as db_transaction
from django import forms
from .models import Wallet, Transaction, CatalogItem, PlayerInventory, DailyReward


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display  = ['player', 'coins', 'gems', 'tickets', 'updated_at']
    search_fields = ['player__id']
    readonly_fields = ['player', 'updated_at']

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        return form


class GrantCurrencyForm(forms.Form):
    currency = forms.ChoiceField(choices=[('coins','Coins'),('gems','Gems'),('tickets','Tickets')])
    amount   = forms.IntegerField(min_value=1)
    reason   = forms.CharField(initial='admin_grant')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display  = ['player', 'type', 'currency', 'amount', 'balance_after', 'reason', 'created_at']
    list_filter   = ['type', 'currency']
    search_fields = ['player__id', 'reason']
    readonly_fields = ['player', 'created_at']


@admin.register(CatalogItem)
class CatalogItemAdmin(admin.ModelAdmin):
    list_display  = ['item_id', 'name', 'category', 'currency', 'price', 'is_available']
    list_filter   = ['category', 'currency', 'is_available']
    search_fields = ['item_id', 'name']
    list_editable = ['price', 'is_available']


@admin.register(PlayerInventory)
class PlayerInventoryAdmin(admin.ModelAdmin):
    list_display  = ['player', 'item', 'quantity', 'acquired_at']
    list_filter   = ['item__category']
    search_fields = ['player__id', 'item__item_id']
    readonly_fields = ['player', 'item', 'acquired_at']


@admin.register(DailyReward)
class DailyRewardAdmin(admin.ModelAdmin):
    list_display = ['player', 'day_streak', 'last_claim', 'updated_at']
    readonly_fields = ['player']
