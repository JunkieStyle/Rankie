import django_tables2 as tables

from django.urls import reverse
from rest_framework import status, viewsets
from django.shortcuts import render
from django.utils.html import format_html
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


# noinspection PyMethodMayBeStatic
class LeagueTable(tables.Table):
    joined = tables.BooleanColumn()
    active = tables.BooleanColumn()

    class Meta:
        model = League
        fields = ("id", "name", "public", "joined", "active", "owner")

    def render_name(self, record, value):
        return format_html("<a href='{}'>{}</a>", reverse("site:league-detail", args=[record.label]), value)

    def render_active(self, record, column, bound_column):
        return column.render(record.is_active(), record, bound_column)

    def render_joined(self, record, column, bound_column):
        value = self.request.user in record.players.all()
        return column.render(value, record, bound_column)


@method_decorator(login_required, name="dispatch")
class LeagueListView(tables.SingleTableMixin, FilterView):
    table_class = LeagueTable
    queryset = League.objects.prefetch_related("players").order_by("-created")
    filterset_class = LeagueFilter
    template_name = "rankie/league/list.html"
    table_pagination = {"per_page": 10}


@method_decorator(login_required, name="dispatch")
class LeagueDetailedView(DetailView):
    template_name = "rankie/league/detail.html"
    model = League
    slug_field = "label"
    slug_url_kwarg = "label"
