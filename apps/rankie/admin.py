from django.contrib import admin
from django.contrib.admin import display

from .models import Game, Round, League, GameRule, Standing, GameResult, LeagueEvent, RoundResult


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("id", "label", "name", "url", "created", "updated")
    list_display_links = ("id", "label", "name")
    date_hierarchy = "created"


@admin.register(GameResult)
class GameResultAdmin(admin.ModelAdmin):
    list_display = ("id", "get_game_label", "player", "origin", "created")
    list_select_related = ("player", "game")
    date_hierarchy = "created"

    @display(ordering="game__label", description="Game")
    def get_game_label(self, obj):
        return obj.game.label


@admin.register(GameRule)
class GameRuleAdmin(admin.ModelAdmin):
    list_display = ("id", "game", "name", "created", "updated")
    list_select_related = ["game"]


@admin.register(League)
class LeagueAdmin(admin.ModelAdmin):
    list_display_links = ("id", "label")
    list_display = ("id", "label", "name", "rule", "owner", "start_dt", "end_dt", "created", "updated")
    list_select_related = ["owner"]


@admin.register(LeagueEvent)
class LeagueEventAdmin(admin.ModelAdmin):
    list_display = ("id", "league", "ev_type", "context")
    list_select_related = ["league"]


@admin.register(Round)
class Round(admin.ModelAdmin):
    list_display_links = ("id", "label")
    list_display = ("id", "label", "league", "mvp")
    list_select_related = ("league", "mvp")


@admin.register(RoundResult)
class RoundResult(admin.ModelAdmin):
    list_display = ("id", "get_round_league", "get_round_label", "player", "score", "raw", "created", "updated")
    list_select_related = ("round__league", "player", "raw")

    @display(ordering="round__label", description="Round")
    def get_round_label(self, obj):
        return obj.round.label

    @display(ordering="round__league", description="League")
    def get_round_league(self, obj):
        return obj.round.league


@admin.register(Standing)
class Standing(admin.ModelAdmin):
    list_display = ("id", "league", "rank", "player", "score", "mvp_count", "created", "updated")
    list_select_related = ("league", "player")
