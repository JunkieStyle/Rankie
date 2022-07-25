from django.contrib import admin
from django.contrib.admin import display

from .models import Game, Round, League, GameRule, Standing, GameResult, RoundResult


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display_links = ["label"]
    list_display = ("label", "name", "url", "created", "updated")
    date_hierarchy = "created"


@admin.register(GameResult)
class GameResultAdmin(admin.ModelAdmin):
    list_display = ("get_game_label", "get_game_round", "get_username", "created")
    list_select_related = ("player", "game")
    date_hierarchy = "created"

    @display(ordering="player__username", description="Player")
    def get_username(self, obj):
        return obj.player.username

    @display(ordering="game__label", description="Game")
    def get_game_label(self, obj):
        return obj.game.label

    @display(ordering="game__round", description="Round")
    def get_game_round(self, obj):
        return obj.game.round


@admin.register(GameRule)
class GameRuleAdmin(admin.ModelAdmin):
    list_display = ("game", "name", "created", "updated")
    list_select_related = ["game"]


@admin.register(League)
class LeagueAdmin(admin.ModelAdmin):
    list_display_links = ("label", "rule")
    list_display = ("label", "name", "rule", "owner", "start_dt", "end_dt", "created", "updated")
    list_select_related = ["owner"]


@admin.register(Round)
class Round(admin.ModelAdmin):
    list_display_links = ("label", "league")
    list_display = ("label", "league", "mvp")
    list_select_related = ("league", "mvp")


@admin.register(RoundResult)
class RoundResult(admin.ModelAdmin):
    list_display_links = ["raw"]
    list_display = ("get_round_league", "get_round_label", "player", "score", "raw", "created", "updated")
    list_select_related = ("round__league", "player", "raw")

    @display(ordering="round__label", description="Round")
    def get_round_label(self, obj):
        return obj.round.label

    @display(ordering="round__league", description="League")
    def get_round_league(self, obj):
        return obj.round.league


@admin.register(Standing)
class Standing(admin.ModelAdmin):
    list_display_links = ["league"]
    list_display = ("league", "rank", "player", "score", "mvp_count", "created", "updated")
    list_select_related = ("league", "player")
