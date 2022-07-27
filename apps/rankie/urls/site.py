from django.urls import path

import apps.rankie.views as views

app_name = "rankie"

urlpatterns = [
    path("", views.index, name="home"),
    path("", views.index, name="profile-detail"),
    path("", views.index, name="send-result"),
    path("leagues/", views.LeagueListView.as_view(), name="league-list"),
    path("leagues/<slug:label>/", views.LeagueDetailedView.as_view(), name="league-detail"),
]
