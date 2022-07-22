from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _


class Game(models.Model):
    name = models.CharField(max_length=32)
    url = models.URLField()

    class Meta:
        db_table = "game"
        verbose_name = _("Game")
        verbose_name_plural = _("Games")


class GameResult(models.Model):
    class ORIGIN(models.TextChoices):
        TG_BOT = "TG_BOT", _("Telegram Bot")
        CUSTOM = "CUSTOM", _("Custom")

    user = models.ForeignKey(to=get_user_model(), on_delete=models.CASCADE, null=False)
    origin = models.CharField(max_length=32, choices=ORIGIN.choices, null=False, blank=False)
    text = models.TextField(null=False)
    game = models.ForeignKey(to=Game, on_delete=models.CASCADE, null=False)

    class Meta:
        db_table = "game_result"
        verbose_name = _("Game result")
        verbose_name_plural = _("Games results")
