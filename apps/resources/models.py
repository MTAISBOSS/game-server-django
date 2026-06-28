import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


class Wallet(models.Model):
    player     = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        primary_key=True, related_name='wallet'
    )
    coins      = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
    gems       = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
    tickets    = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wallets'

    def __str__(self):
        return f'{self.player} — coins:{self.coins} gems:{self.gems}'


class Transaction(models.Model):
    TYPES      = [('credit','Credit'),('debit','Debit'),('purchase','Purchase'),('reward','Reward')]
    CURRENCIES = [('coins','Coins'),('gems','Gems'),('tickets','Tickets')]

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player       = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions'
    )
    type         = models.CharField(max_length=20, choices=TYPES)
    currency     = models.CharField(max_length=20, choices=CURRENCIES)
    amount       = models.BigIntegerField()
    balance_after = models.BigIntegerField()
    reason       = models.CharField(max_length=200, blank=True, default='')
    reference_id = models.CharField(max_length=200, blank=True, default='')
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'transactions'
        indexes  = [models.Index(fields=['player', '-created_at'])]
        ordering = ['-created_at']


class CatalogItem(models.Model):
    CURRENCIES = [('coins','Coins'),('gems','Gems'),('tickets','Tickets')]

    item_id      = models.CharField(max_length=100, primary_key=True)
    name         = models.CharField(max_length=200)
    description  = models.TextField(blank=True, default='')
    category     = models.CharField(max_length=50, db_index=True)
    currency     = models.CharField(max_length=20, choices=CURRENCIES)
    price        = models.BigIntegerField()
    is_available = models.BooleanField(default=True, db_index=True)
    metadata     = models.JSONField(default=dict, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'item_catalog'
        ordering = ['category', 'price']

    def __str__(self):
        return f'{self.name} ({self.price} {self.currency})'


class PlayerInventory(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player      = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='inventory'
    )
    item        = models.ForeignKey(CatalogItem, on_delete=models.CASCADE)
    quantity    = models.IntegerField(default=1, validators=[MinValueValidator(0)])
    metadata    = models.JSONField(default=dict, blank=True)
    acquired_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = 'player_inventory'
        unique_together = [['player', 'item']]
        indexes         = [models.Index(fields=['player'])]


class DailyReward(models.Model):
    player     = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        primary_key=True, related_name='daily_reward'
    )
    last_claim = models.DateTimeField(null=True, blank=True)
    day_streak = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'daily_rewards'
