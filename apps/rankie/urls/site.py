from django.urls import path

import apps.rankie.views as views

app_name = "rankie"

urlpatterns = [
    path("", views.index, name="home"),
    path("", views.index, name="profile-detail"),
    path("", views.index, name="send-result"),
    path("leagues/", views.LeagueListView.as_view(), name="league-list"),
    path("leagues/<slug:label>/", views.LeagueDetailedView.as_view(), name="league-detail"),
    path("leagues/<slug:label>/standings/", views.LeagueStandingsView.as_view(), name="league-standings"),
    path("leagues/<slug:label>/rounds/", views.LeagueRoundsView.as_view(), name="league-rounds"),
    path("leagues/<slug:label>/rounds/<str:round_label>/", views.LeagueRoundResultsView.as_view(), name="league-round"),
    path("leagues/<slug:label>/events/", views.LeagueEventsView.as_view(), name="league-events"),
    path("leagues/<slug:label>/leave/", views.LeaveLeagueView.as_view(), name="league-leave"),
    path("leagues/<slug:label>/join/", views.JoinLeagueView.as_view(), name="league-join"),
    path("leagues/<slug:label>/edit/", views.EditLeagueView.as_view(), name="league-edit"),
]
