import django_tables2 as tables

from django.db import transaction
from rest_framework import status, viewsets
from django.db.models import F, Q, Prefetch
from django.shortcuts import render
from django.views.generic import DetailView
from django_filters.views import FilterView
from django.utils.decorators import method_decorator
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth.decorators import login_required

from .core import register_game_result
from .models import Round, League, Standing, GameResult, LeagueEvent, RoundResult
from .tables import LeagueTable, LeagueEventTable, LeagueRoundTable, RoundResultTable, LeagueStandingTable
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


@method_decorator(login_required, name="dispatch")
class LeagueListView(tables.SingleTableMixin, FilterView):
    table_class = LeagueTable
    queryset = League.objects.select_related("rule__game").prefetch_related("players").order_by("-created")
    filterset_class = LeagueFilter
    template_name = "rankie/league/list.html"
    table_pagination = {"per_page": 10}


@method_decorator(login_required, name="dispatch")
class LeagueDetailedView(tables.MultiTableMixin, DetailView):
    template_name = "rankie/league/detail.html"
    model = League
    slug_field = "label"
    slug_url_kwarg = "label"
    table_pagination = False

    def get_tables(self):
        league = self.get_object()
        return [
            LeagueStandingTable(
                Standing.objects.filter(league=league)
                .filter(Q(rank__in=[1, 2, 3]) | Q(player=self.request.user))
                .select_related("player")
                .order_by(F("rank").asc(nulls_last=True))
            ),
            LeagueEventTable(LeagueEvent.objects.filter(league=league).order_by("-created")[:5]),
            LeagueRoundTable(
                Round.objects.filter(league=league)
                .select_related("mvp")
                .prefetch_related(
                    Prefetch("round_results", RoundResult.objects.order_by("-score"), to_attr="mvp_results")
                )
                .order_by("-label")[:4]
            ),
        ]


@method_decorator(login_required, name="dispatch")
class LeagueStandingsView(tables.SingleTableMixin, DetailView):
    template_name = "rankie/league/standings.html"
    model = League
    slug_field = "label"
    slug_url_kwarg = "label"
    table_class = LeagueStandingTable
    table_pagination = {"per_page": 10}

    def get_table_data(self):
        league = self.get_object()
        return league.standings.select_related("player").order_by(F("rank").asc(nulls_last=True))


@method_decorator(login_required, name="dispatch")
class LeagueRoundsView(tables.SingleTableMixin, DetailView):
    template_name = "rankie/league/rounds.html"
    model = League
    slug_field = "label"
    slug_url_kwarg = "label"
    table_class = LeagueRoundTable
    table_pagination = {"per_page": 10}

    def get_table_data(self):
        league = self.get_object()
        return (
            league.rounds.select_related("mvp")
            .prefetch_related(Prefetch("round_results", RoundResult.objects.order_by("-score"), to_attr="mvp_results"))
            .order_by("-label")
        )


# noinspection PyMethodMayBeStatic


class LeagueRoundResultsView(tables.SingleTableMixin, DetailView):
    template_name = "rankie/league/round.html"
    model = League
    slug_field = "label"
    slug_url_kwarg = "label"
    table_class = RoundResultTable
    table_pagination = {"per_page": 10}

    def get_table_data(self):
        return RoundResult.objects.filter(
            round__league=self.object, round__label=self.kwargs.get("round_label")
        ).order_by("-score")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["round_label"] = self.kwargs.get("round_label")
        return context


@method_decorator(login_required, name="dispatch")
class LeagueEventsView(tables.SingleTableMixin, DetailView):
    template_name = "rankie/league/events.html"
    model = League
    slug_field = "label"
    slug_url_kwarg = "label"
    table_class = LeagueEventTable
    table_pagination = {"per_page": 10}

    def get_table_data(self):
        league = self.get_object()
        return league.events.order_by("-created")


@method_decorator(login_required, name="dispatch")
class JoinLeagueView(LeagueDetailedView):
    def get_object(self, **kwargs):
        obj = super().get_object()
        if self.request.user in obj.players.all():
            return obj

        with transaction.atomic():
            obj.players.add(self.request.user)
            obj.events.create(ev_type=LeagueEvent.EV_TYPE.NEW_PLAYER, context={"username": self.request.user.username})
            obj.save()

        return obj


@method_decorator(login_required, name="dispatch")
class LeaveLeagueView(LeagueDetailedView):
    def get_object(self, **kwargs):
        obj = super().get_object()
        if self.request.user not in obj.players.all():
            return obj

        with transaction.atomic():
            obj.players.remove(self.request.user)
            obj.events.create(ev_type=LeagueEvent.EV_TYPE.PLAYER_LEFT, context={"username": self.request.user.username})
            obj.save()

        return obj


@method_decorator(login_required, name="dispatch")
class RefreshLeagueView(LeagueDetailedView):
    def get_object(self, **kwargs):
        obj = super().get_object()
        return obj


@method_decorator(login_required, name="dispatch")
class EditLeagueView(LeagueDetailedView):
    pass
