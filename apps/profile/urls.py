from django.urls import path
from . import views

urlpatterns = [
    path('me',              views.MyProfileView.as_view(),    name='profile-me'),
    path('me/avatar',       views.MyAvatarView.as_view(),     name='profile-avatar'),
    path('me/stats',        views.MyStatsView.as_view(),      name='profile-stats'),
    path('',                views.PlayerSearchView.as_view(), name='profile-search'),
    path('<uuid:player_id>', views.PublicProfileView.as_view(), name='profile-public'),
]
