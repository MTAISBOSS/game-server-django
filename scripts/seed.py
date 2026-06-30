#!/usr/bin/env python
import os, sys, django
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.auth_service.models import Player
from apps.leaderboard.models import Season
from apps.resources.models import CatalogItem

ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin1234')

# ─── Superuser ─────────────────────────────────────────────────────────────────
if not Player.objects.filter(username=ADMIN_USERNAME).exists():
    player = Player(
        username=ADMIN_USERNAME,
        role='admin',
        is_staff=True,
        is_superuser=True,
        is_active=True,
    )
    player.set_password(ADMIN_PASSWORD)
    player.save()
    print(f'[seed] Superuser created: {ADMIN_USERNAME} / {ADMIN_PASSWORD}')
else:
    print(f'[seed] Superuser already exists: {ADMIN_USERNAME}')

# ─── Season ─────────────────────────────────────────────────────────────────────
if not Season.objects.exists():
    now = datetime.now(timezone.utc)
    Season.objects.create(
        name='Season 1',
        starts_at=now,
        ends_at=now + timedelta(days=90),
        is_active=True,
    )
    print('[seed] Season 1 created (active, 90 days)')
else:
    print('[seed] Seasons already exist — skipping')

# ─── Catalog ────────────────────────────────────────────────────────────────────
ITEMS = [
    dict(item_id='avatar_warrior',   name='Warrior Avatar',      description='Fearless warrior skin',          category='avatar',     currency='coins', price=500,  metadata={'rarity': 'common'}),
    dict(item_id='avatar_mage',      name='Mage Avatar',         description='Mystical mage skin',             category='avatar',     currency='coins', price=750,  metadata={'rarity': 'rare'}),
    dict(item_id='avatar_rogue',     name='Rogue Avatar',        description='Stealthy rogue skin',            category='avatar',     currency='coins', price=750,  metadata={'rarity': 'rare'}),
    dict(item_id='frame_gold',       name='Gold Frame',          description='Shiny gold profile frame',       category='frame',      currency='gems',  price=50,   metadata={'rarity': 'rare'}),
    dict(item_id='frame_diamond',    name='Diamond Frame',       description='Prestigious diamond frame',      category='frame',      currency='gems',  price=200,  metadata={'rarity': 'legendary'}),
    dict(item_id='boost_xp_1h',     name='XP Boost 1hr',        description='2x XP for 1 hour',               category='boost',      currency='gems',  price=20,   metadata={'duration_mins': 60, 'multiplier': 2}),
    dict(item_id='boost_xp_24h',    name='XP Boost 24hr',       description='2x XP for 24 hours',             category='boost',      currency='gems',  price=100,  metadata={'duration_mins': 1440, 'multiplier': 2}),
    dict(item_id='ticket_bundle_5',  name='Ticket Bundle x5',   description='Five match tickets',             category='consumable', currency='coins', price=200,  metadata={'quantity': 5}),
    dict(item_id='ticket_bundle_20', name='Ticket Bundle x20',  description='Twenty match tickets',           category='consumable', currency='coins', price=700,  metadata={'quantity': 20}),
]

created = 0
for item_data in ITEMS:
    _, c = CatalogItem.objects.get_or_create(item_id=item_data['item_id'], defaults=item_data)
    if c:
        created += 1

print(f'[seed] Catalog: {created} items created, {len(ITEMS) - created} already existed')
print('[seed] Done.')
