from django.db import models
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Game(models.Model):
    label = models.SlugField(max_length=32, unique=True)
    name = models.CharField(max_length=128, unique=True)
    url = models.URLField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "game"
        verbose_name = _("Game")
        verbose_name_plural = _("Games")

    def __str__(self):
        return self.name


class GameRule(models.Model):
    name = models.CharField(max_length=128)
    game = models.ForeignKey(to=Game, on_delete=models.CASCADE)
    py_class = models.CharField(max_length=256)
    py_kwargs = models.JSONField(default=dict)  # TODO: add validation for only dicts
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "game_rule"
        verbose_name = _("Game rule")
        verbose_name_plural = _("Game rules")
        unique_together = ("game", "name")
        default_related_name = "rules"

    def __str__(self):
        return self.name


class GameResult(models.Model):
    class ORIGIN(models.TextChoices):
        TG_BOT = "TG_BOT", _("Telegram Bot")
        CUSTOM = "CUSTOM", _("Custom")

    player = models.ForeignKey(to=User, on_delete=models.CASCADE, null=False)
    origin = models.CharField(max_length=32, choices=ORIGIN.choices, null=False, blank=False)
    text = models.TextField(null=False)
    game = models.ForeignKey(to=Game, on_delete=models.CASCADE, null=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "game_result"
        verbose_name = _("Game result")
        verbose_name_plural = _("Games results")
        unique_together = ("player", "game", "text")
        default_related_name = "game_results"

    def __str__(self):
        return _(f"{self.player}'s {self.game} result")


class LeagueQuerySet(models.QuerySet):
    @property
    def _active_filter(self):
        now = timezone.now()
        return Q(start_dt__lte=now, end_dt__gt=now) | Q(start_dt__lte=now, end_dt__isnull=True)

    def active(self):
        return self.filter(self._active_filter)

    def inactive(self):
        return self.exclude(self._active_filter)


class League(models.Model):
    label = models.SlugField(max_length=32, unique=True)
    name = models.CharField(max_length=256, unique=True)
    owner = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name="owned_leagues")
    rule = models.ForeignKey(to=GameRule, on_delete=models.CASCADE)
    players = models.ManyToManyField(to=User, through="Standing")
    start_dt = models.DateTimeField()
    end_dt = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = LeagueQuerySet.as_manager()

    class Meta:
        db_table = "league"
        verbose_name = _("League")
        verbose_name_plural = _("Leagues")
        default_related_name = "leagues"

    def __str__(self):
        return self.name

    def is_active(self):
        if self.end_dt is not None:
            return self.start_dt <= timezone.now() < self.end_dt
        return self.start_dt <= timezone.now()


class Round(models.Model):
    label = models.CharField(max_length=128)
    league = models.ForeignKey(to=League, on_delete=models.CASCADE)
    description = models.TextField(null=True, blank=True)
    mvp = models.ForeignKey(to=User, on_delete=models.SET_NULL, default=None, null=True, blank=True)

    class Meta:
        db_table = "round"
        verbose_name = _("Round")
        verbose_name_plural = _("Rounds")
        unique_together = ("label", "league")
        default_related_name = "rounds"

    def __str__(self):
        return _(f"round {self.label} of {self.league}")


class RoundResult(models.Model):
    round = models.ForeignKey(to=Round, on_delete=models.CASCADE)
    player = models.ForeignKey(to=User, on_delete=models.CASCADE)
    score = models.FloatField()
    raw = models.ForeignKey(to=GameResult, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "round_result"
        verbose_name = _("Round result")
        verbose_name_plural = _("Rounds results")
        unique_together = ("round", "player")
        default_related_name = "round_results"

    def __str__(self):
        return _(f"{self.player}'s result for {self.round}")


class Standing(models.Model):
    league = models.ForeignKey(to=League, on_delete=models.CASCADE)
    rank = models.PositiveIntegerField(null=True, blank=True)
    player = models.ForeignKey(to=User, on_delete=models.CASCADE)
    score = models.FloatField(null=True, blank=True)
    mvp_count = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "standing"
        verbose_name = _("Standing")
        verbose_name_plural = _("Standings")
        unique_together = ("player", "league")
        default_related_name = "standings"

    def __str__(self):
        return _(f"{self.player}'s standing in {self.league}")
