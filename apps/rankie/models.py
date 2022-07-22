from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _


class Game(models.Model):
    label = models.SlugField(max_length=32, unique=True)
    name = models.CharField(max_length=128)
    url = models.URLField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "game"
        verbose_name = _("Game")
        verbose_name_plural = _("Games")

    def __str__(self):
        return self.name


class GameResult(models.Model):
    class ORIGIN(models.TextChoices):
        TG_BOT = "TG_BOT", _("Telegram Bot")
        CUSTOM = "CUSTOM", _("Custom")

    user = models.ForeignKey(to=get_user_model(), on_delete=models.CASCADE, null=False)
    origin = models.CharField(max_length=32, choices=ORIGIN.choices, null=False, blank=False)
    text = models.TextField(null=False)
    game = models.ForeignKey(to=Game, on_delete=models.CASCADE, null=False)
    round = models.PositiveIntegerField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "game_result"
        unique_together = ("user", "game", "round")
        verbose_name = _("Game result")
        verbose_name_plural = _("Games results")
