from django.db import transaction
from django.utils import timezone
from django.core.cache import cache
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.auth_service.schema_serializers import ErrorResponseSerializer
from .models import Wallet, Transaction, CatalogItem, PlayerInventory, DailyReward
from .serializers import (
    WalletSerializer, TransactionSerializer, CatalogItemSerializer,
    InventoryItemSerializer, DailyRewardResultSerializer,
)
from .schema_serializers import (
    CurrencyRequestSerializer, SpendResponseSerializer,
    ConsumeRequestSerializer, ConsumeResponseSerializer,
    PurchaseRequestSerializer, PurchaseResponseSerializer,
    InventoryResponseSerializer,
)

DAILY_REWARDS = [
    {'coins': 100, 'gems': 0},
    {'coins': 150, 'gems': 0},
    {'coins': 200, 'gems': 5},
    {'coins': 250, 'gems': 5},
    {'coins': 300, 'gems': 10},
    {'coins': 400, 'gems': 10},
    {'coins': 500, 'gems': 20},
]


def get_or_create_wallet(player):
    wallet, _ = Wallet.objects.get_or_create(player=player)
    return wallet


def record_transaction(player, tx_type, currency, amount, balance_after, reason='', reference_id=''):
    Transaction.objects.create(
        player=player, type=tx_type, currency=currency,
        amount=amount, balance_after=balance_after,
        reason=reason, reference_id=reference_id,
    )


# ── Wallet ───────────────────────────────────────────────────────────────────

class WalletView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id='wallet_get',
        summary='Get wallet',
        description='Get the current player\'s wallet balance (coins, gems, tickets).',
        responses={200: WalletSerializer},
        tags=['Resources'],
    )
    def get(self, request):
        wallet = get_or_create_wallet(request.user)
        return Response(WalletSerializer(wallet).data)


class AddCurrencyView(APIView):
    """Internal/admin use — add currency to a player's wallet."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id='wallet_add',
        summary='Add currency',
        description='Add currency (coins, gems, or tickets) to the player\'s wallet.',
        request=CurrencyRequestSerializer,
        responses={200: WalletSerializer, 400: ErrorResponseSerializer},
        tags=['Resources'],
    )
    def post(self, request):
        currency = request.data.get('currency')
        amount   = int(request.data.get('amount', 0))
        reason   = request.data.get('reason', 'add')

        if currency not in ('coins', 'gems', 'tickets'):
            return Response({'error': 'Invalid currency'}, status=400)
        if amount <= 0:
            return Response({'error': 'Amount must be positive'}, status=400)

        with transaction.atomic():
            wallet = Wallet.objects.select_for_update().get_or_create(player=request.user)[0]
            setattr(wallet, currency, getattr(wallet, currency) + amount)
            wallet.save(update_fields=[currency, 'updated_at'])
            record_transaction(request.user, 'credit', currency, amount, getattr(wallet, currency), reason)

        return Response(WalletSerializer(wallet).data)


class SpendCurrencyView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id='wallet_spend',
        summary='Spend currency',
        description='Spend currency (coins, gems, or tickets) from the player\'s wallet. '
                    'Returns error if insufficient balance.',
        request=CurrencyRequestSerializer,
        responses={200: SpendResponseSerializer, 400: ErrorResponseSerializer},
        tags=['Resources'],
    )
    def post(self, request):
        currency = request.data.get('currency')
        amount   = int(request.data.get('amount', 0))
        reason   = request.data.get('reason', 'spend')

        if currency not in ('coins', 'gems', 'tickets'):
            return Response({'error': 'Invalid currency'}, status=400)
        if amount <= 0:
            return Response({'error': 'Amount must be positive'}, status=400)

        with transaction.atomic():
            wallet = Wallet.objects.select_for_update().get_or_create(player=request.user)[0]
            current = getattr(wallet, currency)
            if current < amount:
                return Response({'success': False, 'error': f'Insufficient {currency}'})
            setattr(wallet, currency, current - amount)
            wallet.save(update_fields=[currency, 'updated_at'])
            record_transaction(request.user, 'debit', currency, amount, getattr(wallet, currency), reason)

        return Response({'success': True, 'updated_wallet': WalletSerializer(wallet).data})


# ── Inventory ────────────────────────────────────────────────────────────────

class InventoryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id='inventory_get',
        summary='Get inventory',
        description='Get the current player\'s inventory (items with quantity > 0).',
        responses={200: InventoryResponseSerializer},
        tags=['Resources'],
    )
    def get(self, request):
        items = PlayerInventory.objects.filter(
            player=request.user, quantity__gt=0
        ).select_related('item').order_by('-acquired_at')
        return Response({'player_id': str(request.user.id), 'items': InventoryItemSerializer(items, many=True).data})


class ConsumeItemView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id='inventory_consume',
        summary='Consume item',
        description='Use/consume items from inventory. Decreases the quantity.',
        request=ConsumeRequestSerializer,
        responses={200: ConsumeResponseSerializer, 404: ErrorResponseSerializer},
        tags=['Resources'],
    )
    def post(self, request, inventory_id):
        quantity = int(request.data.get('quantity', 1))
        try:
            inv = PlayerInventory.objects.select_for_update().get(
                id=inventory_id, player=request.user
            )
        except PlayerInventory.DoesNotExist:
            return Response({'success': False, 'error': 'Item not found'}, status=404)

        if inv.quantity < quantity:
            return Response({'success': False, 'error': 'Insufficient quantity'})

        inv.quantity -= quantity
        inv.save(update_fields=['quantity'])
        return Response({'success': True, 'remaining': inv.quantity})


# ── Catalog / Shop ───────────────────────────────────────────────────────────

class CatalogView(generics.ListAPIView):
    permission_classes  = [IsAuthenticated]
    serializer_class    = CatalogItemSerializer
    queryset            = CatalogItem.objects.none()  # prevents AnonymousUser error in schema gen

    @extend_schema(
        operation_id='catalog_list',
        summary='Browse catalog',
        description='Get available catalog items, optionally filtered by category.',
        parameters=[
            OpenApiParameter('category', str, OpenApiParameter.QUERY,
                             description='Filter by category', required=False),
        ],
        responses={200: CatalogItemSerializer(many=True)},
        tags=['Resources'],
    )
    def get_queryset(self):
        qs = CatalogItem.objects.filter(is_available=True)
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)
        return qs


class PurchaseItemView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id='catalog_purchase',
        summary='Purchase item',
        description='Purchase an item from the catalog. Deducts currency from wallet '
                    'and adds the item to inventory.',
        request=PurchaseRequestSerializer,
        responses={200: PurchaseResponseSerializer, 404: ErrorResponseSerializer},
        tags=['Resources'],
    )
    def post(self, request, item_id):
        quantity = int(request.data.get('quantity', 1))
        try:
            item = CatalogItem.objects.get(item_id=item_id, is_available=True)
        except CatalogItem.DoesNotExist:
            return Response({'success': False, 'error': 'Item not available'}, status=404)

        total_cost = item.price * quantity

        with transaction.atomic():
            wallet = Wallet.objects.select_for_update().get_or_create(player=request.user)[0]
            current = getattr(wallet, item.currency)
            if current < total_cost:
                return Response({'success': False, 'error': f'Insufficient {item.currency}'})

            setattr(wallet, item.currency, current - total_cost)
            wallet.save(update_fields=[item.currency, 'updated_at'])
            record_transaction(request.user, 'purchase', item.currency, total_cost,
                               getattr(wallet, item.currency), f'purchase:{item_id}')

            inv, _ = PlayerInventory.objects.get_or_create(
                player=request.user, item=item, defaults={'quantity': 0}
            )
            inv.quantity += quantity
            inv.save(update_fields=['quantity'])

        return Response({
            'success':        True,
            'updated_wallet': WalletSerializer(wallet).data,
            'item':           InventoryItemSerializer(inv).data,
        })


# ── Transactions ─────────────────────────────────────────────────────────────

class TransactionListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class   = TransactionSerializer
    queryset           = Transaction.objects.none()  # prevents AnonymousUser error in schema gen

    @extend_schema(
        operation_id='transactions_list',
        summary='Transaction history',
        description='Get the current player\'s transaction history (paginated).',
        parameters=[
            OpenApiParameter('page', int, OpenApiParameter.QUERY, description='Page number', default=1),
        ],
        responses={200: TransactionSerializer(many=True)},
        tags=['Resources'],
    )
    def get_queryset(self):
        return Transaction.objects.filter(player=self.request.user)

    def list(self, request, *args, **kwargs):
        qs    = Transaction.objects.filter(player=request.user)
        page  = self.paginate_queryset(qs)
        ser   = self.get_serializer(page, many=True)
        return self.get_paginated_response(ser.data)


# ── Daily Reward ────────────────────────────────────────────────────────────

class DailyRewardView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id='daily_reward',
        summary='Claim daily reward',
        description='Claim the daily login reward. Rewards scale with consecutive login streak '
                    '(up to 7 days, then resets). Can only be claimed once per day.',
        request=None,
        responses={200: DailyRewardResultSerializer},
        tags=['Resources'],
    )
    def post(self, request):
        now        = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow   = today_start + timezone.timedelta(days=1)
        yesterday  = today_start - timezone.timedelta(days=1)

        reward_obj, _ = DailyReward.objects.get_or_create(player=request.user)

        if reward_obj.last_claim and reward_obj.last_claim >= today_start:
            return Response({
                'already_claimed': True,
                'day_streak':      reward_obj.day_streak,
                'coins_earned':    0,
                'gems_earned':     0,
                'next_claim_at':   int(tomorrow.timestamp() * 1000),
            })

        streak_valid = reward_obj.last_claim and reward_obj.last_claim >= yesterday
        new_streak   = (reward_obj.day_streak % 7) + 1 if streak_valid else 1
        reward       = DAILY_REWARDS[new_streak - 1]

        with transaction.atomic():
            reward_obj.last_claim = now
            reward_obj.day_streak = new_streak
            reward_obj.save()

            wallet = Wallet.objects.select_for_update().get_or_create(player=request.user)[0]
            if reward['coins']:
                wallet.coins += reward['coins']
            if reward['gems']:
                wallet.gems += reward['gems']
            wallet.save(update_fields=['coins', 'gems', 'updated_at'])

            if reward['coins']:
                record_transaction(request.user, 'reward', 'coins',
                                   reward['coins'], wallet.coins, 'daily_reward')
            if reward['gems']:
                record_transaction(request.user, 'reward', 'gems',
                                   reward['gems'], wallet.gems, 'daily_reward')

        return Response({
            'already_claimed': False,
            'day_streak':      new_streak,
            'coins_earned':    reward['coins'],
            'gems_earned':     reward['gems'],
            'next_claim_at':   int(tomorrow.timestamp() * 1000),
        })
