from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth_service', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CatalogItem',
            fields=[
                ('item_id', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True, default='')),
                ('category', models.CharField(db_index=True, max_length=50)),
                ('currency', models.CharField(choices=[('coins', 'Coins'), ('gems', 'Gems'), ('tickets', 'Tickets')], max_length=20)),
                ('price', models.BigIntegerField()),
                ('is_available', models.BooleanField(db_index=True, default=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'item_catalog',
                'ordering': ['category', 'price'],
            },
        ),
        migrations.CreateModel(
            name='Wallet',
            fields=[
                ('player', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='wallet', serialize=False, to=settings.AUTH_USER_MODEL)),
                ('coins', models.BigIntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('gems', models.BigIntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('tickets', models.BigIntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'wallets',
            },
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('type', models.CharField(choices=[('credit', 'Credit'), ('debit', 'Debit'), ('purchase', 'Purchase'), ('reward', 'Reward')], max_length=20)),
                ('currency', models.CharField(choices=[('coins', 'Coins'), ('gems', 'Gems'), ('tickets', 'Tickets')], max_length=20)),
                ('amount', models.BigIntegerField()),
                ('balance_after', models.BigIntegerField()),
                ('reason', models.CharField(blank=True, default='', max_length=200)),
                ('reference_id', models.CharField(blank=True, default='', max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'transactions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['player', '-created_at'], name='tx_player_idx'),
        ),
        migrations.CreateModel(
            name='PlayerInventory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('quantity', models.IntegerField(default=1, validators=[django.core.validators.MinValueValidator(0)])),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('acquired_at', models.DateTimeField(auto_now_add=True)),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='resources.catalogitem')),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inventory', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'player_inventory',
                'unique_together': {('player', 'item')},
            },
        ),
        migrations.AddIndex(
            model_name='playerinventory',
            index=models.Index(fields=['player'], name='inv_player_idx'),
        ),
        migrations.CreateModel(
            name='DailyReward',
            fields=[
                ('player', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='daily_reward', serialize=False, to=settings.AUTH_USER_MODEL)),
                ('last_claim', models.DateTimeField(blank=True, null=True)),
                ('day_streak', models.IntegerField(default=0)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'daily_rewards',
            },
        ),
    ]
