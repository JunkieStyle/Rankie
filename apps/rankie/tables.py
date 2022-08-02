import django_tables2 as tables

from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.rankie.models import Round, League, Standing, LeagueEvent, RoundResult


class LeagueTable(tables.Table):
    game = tables.Column(empty_values=())

    class Meta:
        model = League
        fields = ("id", "name", "game")

    def render_name(self, record, value):
        return format_html("<a href='{}'>{}</a>", reverse("site:league-detail", args=[record.label]), value)

    def render_game(self, record):
        return record.rule.game


class LeagueStandingTable(tables.Table):
    mvp_count = tables.Column(verbose_name="MVPs", attrs={"td": {"class": "icon"}})

    class Meta:
        model = Standing
        fields = ("rank", "player", "score", "mvp_count")
        orderable = False

    def render_score(self, value):
        return round(value, 3)

    def render_mvp_count(self, value):
        return format_html('{} <i class="fa-solid fa-star text-warning fa-md"></i>', value)


class LeagueRoundTable(tables.Table):
    mvp = tables.Column(verbose_name="MVP")
    score = tables.Column(empty_values=())

    class Meta:
        model = Round
        fields = ("label", "mvp", "score")
        orderable = False

    def render_score(self, record):
        return round(record.mvp_results[0].score, 3)

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


class RoundResultTable(tables.Table):
    class Meta:
        model = RoundResult
        fields = ("player", "score", "created")
        orderable = False
