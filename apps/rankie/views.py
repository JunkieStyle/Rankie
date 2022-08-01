import django_tables2 as tables

from django.urls import reverse
from rest_framework import status, viewsets
from django.db.models import F, Q, Prefetch
from django.shortcuts import render
from django.utils.html import format_html
from django.views.generic import DetailView
from django_filters.views import FilterView
from django.utils.decorators import method_decorator
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from rest_framework.decorators import action
from django.contrib.auth.decorators import login_required

from .core import register_game_result
from .models import Round, League, Standing, GameResult, LeagueEvent, RoundResult
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
    game = tables.Column(empty_values=())

    class Meta:
        model = League
        fields = ("id", "name", "game")

    def render_name(self, record, value):
        return format_html("<a href='{}'>{}</a>", reverse("site:league-detail", args=[record.label]), value)

    def render_game(self, record):
        return record.rule.game


@method_decorator(login_required, name="dispatch")
class LeagueListView(tables.SingleTableMixin, FilterView):
    table_class = LeagueTable
    queryset = League.objects.select_related("rule__game").prefetch_related("players").order_by("-created")
    filterset_class = LeagueFilter
    template_name = "rankie/league/list.html"
    table_pagination = {"per_page": 10}


# noinspection PyMethodMayBeStatic
class LeagueStandingTable(tables.Table):
    mvp_count = tables.Column(verbose_name="MVPs", attrs={"td": {"class": "icon"}})

    class Meta:
        model = Standing
        fields = ("rank", "player", "score", "mvp_count")
        orderable = False

    def render_mvp_count(self, value):
        return format_html('{} <i class="fa-solid fa-star text-warning fa-md"></i>', value)


# noinspection PyMethodMayBeStatic
class LeagueRoundTable(tables.Table):
    mvp = tables.Column(verbose_name="MVP")
    score = tables.Column(empty_values=())

    class Meta:
        model = Round
        fields = ("label", "mvp", "score")
        orderable = False

    def render_score(self, record):
        return record.mvp_results[0].score

    def render_label(self, record, value):
        return format_html(
            "<a href='{}'>{}</a>", reverse("site:league-round", args=(record.league.label, value)), value
        )


class LeagueEventTable(tables.Table):
    EV_TYPE_MESSAGES = {
        "NEW_LEADER": _("Wow! We have a new leader, <span class='text-primary'>@{username}</span> has taken a lead!"),
        "NEW_SCORE": _(
            """Registered new score, <span class='text-primary'>@{username}</span> earned
            <span class='text-info'>{score}</span> point(s) for <span class='text-info'>round {round_label}</span>."""
        ),
        "NEW_PLAYER": _("New player has joined the league, <span class='text-primary'>@{username}</span> welcome!"),
        "NEW_MVP": _(
            """Wow! <span class='text-primary'>@{username}</span> earned MVP
            for <span class='text-info'>round {round_label}</span>!"""
        ),
        "PLAYER_LEFT": _(
            "Unfortunately, <span class='text-primary'>@{username}</span> has left the league, we will miss you!"
        ),
        "LEAGUE_FINISHED": _(
            "League has finished! Congratulations to the winner: <span class='text-primary'>@{username}</span>!"
        ),
    }
    EV_TYPE_ICONS = {
        "NEW_LEADER": '<i class="fa-solid fa-medal fa-lg text-warning"></i>',
        "NEW_SCORE": '<i class="fa-solid fa-circle-plus fa-lg text-info"></i>',
        "NEW_PLAYER": '<i class="fa-solid fa-user-plus fa-lg text-success"></i>',
        "NEW_MVP": '<i class="fa-solid fa-star fa-lg text-warning"></i>',
        "PLAYER_LEFT": '<i class="fa-solid fa-user-minus fa-lg text-danger"></i>',
        "LEAGUE_FINISHED": '<i class="fa-solid fa-trophy fa-lg text-warning"></i>',
    }
    icon = tables.Column(empty_values=(), attrs={"td": {"class": "icon"}})
    datetime = tables.Column(empty_values=())
    message = tables.Column(empty_values=())

    class Meta:
        model = LeagueEvent
        fields = ("icon", "datetime", "message")
        orderable = False
        show_header = False

    def render_icon(self, record):
        return format_html(self.EV_TYPE_ICONS[record.ev_type])

    # noinspection PyMethodMayBeStatic
    def render_datetime(self, record):
        return record.created

    def render_message(self, record):
        return format_html(self.EV_TYPE_MESSAGES[record.ev_type], **record.context)


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
class RoundResultTable(tables.Table):
    class Meta:
        model = RoundResult
        fields = ("player", "score", "created")
        orderable = False


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
        obj.players.add(self.request.user)
        obj.save()
        return obj


@method_decorator(login_required, name="dispatch")
class LeaveLeagueView(LeagueDetailedView):
    def get_object(self, **kwargs):
        obj = super().get_object()
        obj.players.remove(self.request.user)
        obj.save()
        return obj


@method_decorator(login_required, name="dispatch")
class EditLeagueView(LeagueDetailedView):
    pass
