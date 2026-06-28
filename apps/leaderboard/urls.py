from django.urls import path
from . import views

urlpatterns = [
    path('',                        views.GlobalBoardView.as_view(),   name='lb-global'),
    path('top',                     views.TopPlayersView.as_view(),    name='lb-top'),
    path('me',                      views.MyRankView.as_view(),        name='lb-me'),
    path('score',                   views.SubmitScoreView.as_view(),   name='lb-score'),
    path('friends',                 views.FriendsBoardView.as_view(),  name='lb-friends'),
    path('seasons',                 views.SeasonListView.as_view(),    name='lb-seasons'),
    path('seasons/current',         views.CurrentSeasonView.as_view(), name='lb-season-current'),
    path('seasons/<uuid:season_id>', views.SeasonBoardView.as_view(),  name='lb-season-board'),
]
