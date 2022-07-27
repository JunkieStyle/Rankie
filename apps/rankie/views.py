import django_tables2 as tables

from rest_framework import status, viewsets
from django.shortcuts import render
from django.views.generic import DetailView
from django_filters.views import FilterView
from django.utils.decorators import method_decorator
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth.decorators import login_required

from .core import register_game_result
from .models import League, GameResult
from .filters import LeagueFilter
from .serializers import GameResultModelSerializer


def index(request):
    return render(request, "rankie/index.html")


class GameResultViewSet(viewsets.ModelViewSet):
    queryset = GameResult.objects.all()
    serializer_class = GameResultModelSerializer

    @action(methods=["GET"], detail=True)
    def register(self, request, *args, **kwargs):
        game_result = self.get_object()
        register_game_result(game_result)
        return Response(status=status.HTTP_200_OK)


class LeagueTable(tables.Table):
    class Meta:
        model = League
        template_name = "django_tables2/bootstrap4.html"
        fields = ("id", "name", "owner", "start_dt", "end_dt")


@method_decorator(login_required, name="dispatch")
class LeagueListView(tables.SingleTableMixin, FilterView):
    table_class = LeagueTable
    queryset = League.objects.all()
    filterset_class = LeagueFilter
    template_name = "rankie/league/list.html"


@method_decorator(login_required, name="dispatch")
class LeagueDetailedView(DetailView):
    template_name = "rankie/league/detail.html"
