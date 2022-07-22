from django.contrib import admin
from django.contrib.admin import display

from .models import Game, GameResult


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("label", "name", "url", "created", "updated")
    date_hierarchy = "created"


@admin.register(GameResult)
class GameResultAdmin(admin.ModelAdmin):
    list_display = ("get_game_label", "get_game_round", "get_username", "created")
    date_hierarchy = "created"

    @display(ordering="user__username", description="User")
    def get_username(self, obj):
        return obj.user.username

    @display(ordering="game__label", description="Game")
    def get_game_label(self, obj):
        return obj.game.label

    @display(ordering="game__round", description="Round")
    def get_game_round(self, obj):
        return obj.game.round
