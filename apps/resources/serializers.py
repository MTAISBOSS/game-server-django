from rest_framework import serializers
from .models import Wallet, Transaction, CatalogItem, PlayerInventory


class WalletSerializer(serializers.ModelSerializer):
    player_id = serializers.UUIDField(source='player_id', read_only=True)
    class Meta:
        model  = Wallet
        fields = ['player_id', 'coins', 'gems', 'tickets', 'updated_at']


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Transaction
        fields = ['id', 'type', 'currency', 'amount', 'balance_after', 'reason', 'created_at']


class CatalogItemSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CatalogItem
        fields = ['item_id', 'name', 'description', 'category', 'currency', 'price', 'is_available', 'metadata']


class InventoryItemSerializer(serializers.ModelSerializer):
    item_id   = serializers.CharField(source='item.item_id')
    item_name = serializers.CharField(source='item.name')
    category  = serializers.CharField(source='item.category')

    class Meta:
        model  = PlayerInventory
        fields = ['id', 'item_id', 'item_name', 'category', 'quantity', 'metadata', 'acquired_at']


class DailyRewardResultSerializer(serializers.Serializer):
    already_claimed = serializers.BooleanField()
    day_streak      = serializers.IntegerField()
    coins_earned    = serializers.IntegerField()
    gems_earned     = serializers.IntegerField()
    next_claim_at   = serializers.IntegerField()
