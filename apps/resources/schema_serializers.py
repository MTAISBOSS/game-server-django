"""
Shared serializer classes used only for OpenAPI schema generation.
Defined once here (not inline) to avoid drf-spectacular name collisions.
"""
from rest_framework import serializers
from .serializers import WalletSerializer, InventoryItemSerializer


class CurrencyRequestSerializer(serializers.Serializer):
    """Request body for add/spend currency."""
    currency = serializers.ChoiceField(choices=['coins', 'gems', 'tickets'])
    amount   = serializers.IntegerField()
    reason   = serializers.CharField(required=False, default='add')


class SpendResponseSerializer(serializers.Serializer):
    """Response for spend currency."""
    success        = serializers.BooleanField()
    error          = serializers.CharField(required=False)
    updated_wallet = WalletSerializer()


class ConsumeRequestSerializer(serializers.Serializer):
    """Request body for consume item."""
    quantity = serializers.IntegerField(required=False, default=1)


class ConsumeResponseSerializer(serializers.Serializer):
    """Response for consume item."""
    success   = serializers.BooleanField()
    remaining = serializers.IntegerField()
    error     = serializers.CharField(required=False)


class PurchaseRequestSerializer(serializers.Serializer):
    """Request body for purchase item."""
    quantity = serializers.IntegerField(required=False, default=1)


class PurchaseResponseSerializer(serializers.Serializer):
    """Response for purchase item."""
    success        = serializers.BooleanField()
    error          = serializers.CharField(required=False)
    updated_wallet = WalletSerializer()
    item           = InventoryItemSerializer()


class InventoryResponseSerializer(serializers.Serializer):
    """Inventory response."""
    player_id = serializers.UUIDField()
    items     = InventoryItemSerializer(many=True)
