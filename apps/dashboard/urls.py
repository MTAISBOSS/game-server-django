from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('',                                    views.home,            name='home'),
    path('login/',                              views.login_view,      name='login'),
    path('logout/',                             views.logout_view,     name='logout'),

    # Players
    path('players/',                            views.players,         name='players'),
    path('players/<uuid:player_id>/',           views.player_detail,   name='player-detail'),
    path('players/<uuid:player_id>/ban/',       views.player_ban,      name='player-ban'),
    path('players/<uuid:player_id>/unban/',     views.player_unban,    name='player-unban'),
    path('players/<uuid:player_id>/grant-currency/', views.grant_currency, name='grant-currency'),
    path('players/<uuid:player_id>/grant-item/', views.grant_item,     name='grant-item'),

    # Leaderboard
    path('leaderboard/',                        views.leaderboard,     name='leaderboard'),
    path('seasons/',                            views.seasons,         name='seasons'),
    path('seasons/create/',                     views.season_create,   name='season-create'),
    path('seasons/<uuid:season_id>/activate/',  views.season_activate, name='season-activate'),
    path('seasons/<uuid:season_id>/delete/',    views.season_delete,   name='season-delete'),

    # Resources
    path('catalog/',                            views.catalog,         name='catalog'),
    path('catalog/create/',                     views.catalog_create,  name='catalog-create'),
    path('catalog/<str:item_id>/toggle/',       views.catalog_toggle,  name='catalog-toggle'),
    path('catalog/<str:item_id>/delete/',       views.catalog_delete,  name='catalog-delete'),

    # Live API
    path('api/stats/',                          views.api_stats,       name='api-stats'),
]
