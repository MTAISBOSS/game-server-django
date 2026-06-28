import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Sum, Avg, Q
from django.db.models.functions import TruncDay, TruncHour
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from datetime import timedelta

from apps.auth_service.models import Player
from apps.profile.models import Profile, PlayerStats
from apps.leaderboard.models import Season, LeaderboardEntry, ScoreHistory
from apps.resources.models import Wallet, Transaction, CatalogItem, PlayerInventory, DailyReward


def is_staff(user):
    return user.is_authenticated and (user.is_staff or user.role == 'admin')


def staff_required(view_func):
    return login_required(user_passes_test(is_staff)(view_func))


# ─── Auth ─────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated and is_staff(request.user):
        return redirect('dashboard:home')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        # USERNAME_FIELD is 'id' (a UUIDField), so look up by username first
        try:
            player = Player.objects.get(username=username)
            user = authenticate(request, username=str(player.id), password=password)
        except Player.DoesNotExist:
            user = None
        if user and is_staff(user):
            login(request, user)
            return redirect('dashboard:home')
        messages.error(request, 'Invalid credentials or insufficient permissions.')
    return render(request, 'dashboard/login.html')


def logout_view(request):
    logout(request)
    return redirect('dashboard:login')


# ─── Home / Stats ──────────────────────────────────────────────────────────────

@staff_required
def home(request):
    now  = timezone.now()
    day  = now - timedelta(days=1)
    week = now - timedelta(days=7)

    total_players  = Player.objects.count()
    new_today      = Player.objects.filter(created_at__gte=day).count()
    new_this_week  = Player.objects.filter(created_at__gte=week).count()
    banned_players = Player.objects.filter(is_banned=True).count()
    phone_linked   = Player.objects.exclude(phone__isnull=True).exclude(phone='').count()

    active_season  = Season.get_active()
    total_scores   = LeaderboardEntry.objects.filter(season=active_season).count() if active_season else 0
    avg_score      = LeaderboardEntry.objects.filter(season=active_season).aggregate(a=Avg('score'))['a'] or 0

    total_coins  = Wallet.objects.aggregate(s=Sum('coins'))['s'] or 0
    total_gems   = Wallet.objects.aggregate(s=Sum('gems'))['s'] or 0
    transactions_today = Transaction.objects.filter(created_at__gte=day).count()

    # Registrations over last 7 days for chart
    reg_chart = (
        Player.objects
        .filter(created_at__gte=week)
        .annotate(day=TruncDay('created_at'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )

    # Score submissions over last 24h
    score_chart = (
        ScoreHistory.objects
        .filter(created_at__gte=day)
        .annotate(hour=TruncHour('created_at'))
        .values('hour')
        .annotate(count=Count('id'))
        .order_by('hour')
    )

    ctx = {
        'total_players':       total_players,
        'new_today':           new_today,
        'new_this_week':       new_this_week,
        'banned_players':      banned_players,
        'phone_linked':        phone_linked,
        'active_season':       active_season,
        'total_scores':        total_scores,
        'avg_score':           round(avg_score),
        'total_coins':         total_coins,
        'total_gems':          total_gems,
        'transactions_today':  transactions_today,
        'reg_chart':           json.dumps([{'day': str(r['day'].date()), 'count': r['count']} for r in reg_chart]),
        'score_chart':         json.dumps([{'hour': str(r['hour'].hour) + 'h', 'count': r['count']} for r in score_chart]),
    }
    return render(request, 'dashboard/home.html', ctx)


# ─── Players ──────────────────────────────────────────────────────────────────

@staff_required
def players(request):
    q       = request.GET.get('q', '')
    role    = request.GET.get('role', '')
    banned  = request.GET.get('banned', '')

    qs = Player.objects.select_related('profile').order_by('-created_at')
    if q:
        qs = qs.filter(Q(device_id__icontains=q) | Q(phone__icontains=q) | Q(profile__username__icontains=q))
    if role:
        qs = qs.filter(role=role)
    if banned == '1':
        qs = qs.filter(is_banned=True)
    elif banned == '0':
        qs = qs.filter(is_banned=False)

    paginator = Paginator(qs, 50)
    page_obj  = paginator.get_page(request.GET.get('page'))

    return render(request, 'dashboard/players.html', {
        'page_obj': page_obj,
        'q': q, 'role': role, 'banned': banned,
    })


@staff_required
def player_detail(request, player_id):
    player  = get_object_or_404(Player, id=player_id)
    profile = getattr(player, 'profile', None)
    stats   = getattr(player, 'stats', None)
    wallet  = getattr(player, 'wallet', None)
    inventory = PlayerInventory.objects.filter(player=player).select_related('item')
    transactions = Transaction.objects.filter(player=player)[:20]

    active_season = Season.get_active()
    lb_entry = None
    lb_rank  = None
    if active_season:
        lb_entry = LeaderboardEntry.objects.filter(player=player, season=active_season).first()
        if lb_entry:
            lb_rank = LeaderboardEntry.objects.filter(
                season=active_season, score__gt=lb_entry.score
            ).count() + 1

    return render(request, 'dashboard/player_detail.html', {
        'player':       player,
        'profile':      profile,
        'stats':        stats,
        'wallet':       wallet,
        'inventory':    inventory,
        'transactions': transactions,
        'lb_entry':     lb_entry,
        'lb_rank':      lb_rank,
    })


@staff_required
@require_POST
def player_ban(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    reason = request.POST.get('reason', '')
    player.is_banned = True
    player.ban_reason = reason
    player.save(update_fields=['is_banned', 'ban_reason'])
    messages.success(request, f'Player {player_id} banned.')
    return redirect('dashboard:player-detail', player_id=player_id)


@staff_required
@require_POST
def player_unban(request, player_id):
    player = get_object_or_404(Player, id=player_id)
    player.is_banned  = False
    player.ban_reason = ''
    player.save(update_fields=['is_banned', 'ban_reason'])
    messages.success(request, f'Player {player_id} unbanned.')
    return redirect('dashboard:player-detail', player_id=player_id)


@staff_required
@require_POST
def grant_currency(request, player_id):
    player   = get_object_or_404(Player, id=player_id)
    currency = request.POST.get('currency')
    amount   = int(request.POST.get('amount', 0))
    reason   = request.POST.get('reason', 'admin_grant')

    if currency not in ('coins', 'gems', 'tickets') or amount <= 0:
        messages.error(request, 'Invalid currency or amount.')
        return redirect('dashboard:player-detail', player_id=player_id)

    wallet, _ = Wallet.objects.get_or_create(player=player)
    setattr(wallet, currency, getattr(wallet, currency) + amount)
    wallet.save(update_fields=[currency, 'updated_at'])
    Transaction.objects.create(
        player=player, type='credit', currency=currency,
        amount=amount, balance_after=getattr(wallet, currency),
        reason=reason, reference_id=f'admin:{request.user.id}',
    )
    messages.success(request, f'Granted {amount} {currency} to player.')
    return redirect('dashboard:player-detail', player_id=player_id)


@staff_required
@require_POST
def grant_item(request, player_id):
    player  = get_object_or_404(Player, id=player_id)
    item_id = request.POST.get('item_id')
    qty     = int(request.POST.get('quantity', 1))

    try:
        item = CatalogItem.objects.get(item_id=item_id)
    except CatalogItem.DoesNotExist:
        messages.error(request, 'Item not found.')
        return redirect('dashboard:player-detail', player_id=player_id)

    inv, _ = PlayerInventory.objects.get_or_create(player=player, item=item, defaults={'quantity': 0})
    inv.quantity += qty
    inv.save(update_fields=['quantity'])
    messages.success(request, f'Granted {qty}x {item.name} to player.')
    return redirect('dashboard:player-detail', player_id=player_id)


# ─── Leaderboard ──────────────────────────────────────────────────────────────

@staff_required
def leaderboard(request):
    seasons = Season.objects.all()
    season_id = request.GET.get('season')
    active_season = Season.get_active()
    season = None

    if season_id:
        season = get_object_or_404(Season, id=season_id)
    else:
        season = active_season

    entries = []
    if season:
        raw = (
            LeaderboardEntry.objects
            .filter(season=season)
            .select_related('player__profile')
            .order_by('-score')[:200]
        )
        for i, e in enumerate(raw, 1):
            profile = getattr(e.player, 'profile', None)
            entries.append({
                'rank':         i,
                'player':       e.player,
                'profile':      profile,
                'score':        e.score,
                'updated_at':   e.updated_at,
            })

    return render(request, 'dashboard/leaderboard.html', {
        'seasons': seasons,
        'season':  season,
        'entries': entries,
    })


@staff_required
def seasons(request):
    all_seasons = Season.objects.annotate(player_count=Count('entries')).order_by('-starts_at')
    return render(request, 'dashboard/seasons.html', {'seasons': all_seasons})


@staff_required
@require_POST
def season_create(request):
    name      = request.POST.get('name')
    starts_at = request.POST.get('starts_at')
    ends_at   = request.POST.get('ends_at')
    is_active = request.POST.get('is_active') == 'on'

    Season.objects.create(
        name=name, starts_at=starts_at,
        ends_at=ends_at, is_active=is_active,
    )
    messages.success(request, f'Season "{name}" created.')
    return redirect('dashboard:seasons')


@staff_required
@require_POST
def season_activate(request, season_id):
    season = get_object_or_404(Season, id=season_id)
    Season.objects.all().update(is_active=False)
    season.is_active = True
    season.save()
    messages.success(request, f'Season "{season.name}" is now active.')
    return redirect('dashboard:seasons')


@staff_required
@require_POST
def season_delete(request, season_id):
    season = get_object_or_404(Season, id=season_id)
    if season.is_active:
        messages.error(request, 'Cannot delete an active season.')
        return redirect('dashboard:seasons')
    season.delete()
    messages.success(request, 'Season deleted.')
    return redirect('dashboard:seasons')


# ─── Resources ────────────────────────────────────────────────────────────────

@staff_required
def catalog(request):
    items = CatalogItem.objects.all().order_by('category', 'price')
    return render(request, 'dashboard/catalog.html', {'items': items})


@staff_required
@require_POST
def catalog_create(request):
    CatalogItem.objects.create(
        item_id     = request.POST.get('item_id'),
        name        = request.POST.get('name'),
        description = request.POST.get('description', ''),
        category    = request.POST.get('category'),
        currency    = request.POST.get('currency'),
        price       = int(request.POST.get('price', 0)),
        is_available = request.POST.get('is_available') == 'on',
    )
    messages.success(request, 'Item created.')
    return redirect('dashboard:catalog')


@staff_required
@require_POST
def catalog_toggle(request, item_id):
    item = get_object_or_404(CatalogItem, item_id=item_id)
    item.is_available = not item.is_available
    item.save(update_fields=['is_available'])
    return JsonResponse({'available': item.is_available})


@staff_required
@require_POST
def catalog_delete(request, item_id):
    item = get_object_or_404(CatalogItem, item_id=item_id)
    item.delete()
    messages.success(request, 'Item deleted.')
    return redirect('dashboard:catalog')


# ─── Live stats API (called by JS) ────────────────────────────────────────────

@staff_required
def api_stats(request):
    now = timezone.now()
    day = now - timedelta(days=1)
    return JsonResponse({
        'total_players':  Player.objects.count(),
        'new_today':      Player.objects.filter(created_at__gte=day).count(),
        'banned':         Player.objects.filter(is_banned=True).count(),
        'transactions_today': Transaction.objects.filter(created_at__gte=day).count(),
        'active_season':  str(Season.get_active()) if Season.get_active() else 'None',
    })
