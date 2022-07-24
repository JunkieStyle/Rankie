from pydoc import locate

from django.db import models
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _


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
    game = models.ForeignKey(to=Game, on_delete=models.CASCADE, related_name="rules")
    python_class = models.CharField(max_length=256)
    greater_is_better = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "game_rule"
        verbose_name = _("Game rule")
        verbose_name_plural = _("Game rules")
        unique_together = ("game", "name")

    def __str__(self):
        return self.name

    def get_scorer(self):
        return locate(self.python_class)()  # noqa


class GameResult(models.Model):
    class ORIGIN(models.TextChoices):
        TG_BOT = "TG_BOT", _("Telegram Bot")
        CUSTOM = "CUSTOM", _("Custom")

    user = models.ForeignKey(to=get_user_model(), on_delete=models.CASCADE, null=False, related_name="results")
    origin = models.CharField(max_length=32, choices=ORIGIN.choices, null=False, blank=False)
    text = models.TextField(null=False)
    game = models.ForeignKey(to=Game, on_delete=models.CASCADE, null=False, related_name="results")
    round = models.PositiveIntegerField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "game_result"
        unique_together = ("user", "game", "round")
        verbose_name = _("Game result")
        verbose_name_plural = _("Games results")

    def is_active(self, league: "League") -> bool:
        return (
            league.is_active()
            and self.created >= league.start_dt
            and (league.end_dt is None or league.end_dt > self.created)
        )


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
    owner = models.ForeignKey(to=get_user_model(), on_delete=models.CASCADE)
    rule = models.ForeignKey(to=GameRule, on_delete=models.CASCADE, related_name="leagues")
    players = models.ManyToManyField(to=get_user_model(), through="Score", related_name="leagues")
    start_dt = models.DateTimeField()
    end_dt = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = LeagueQuerySet.as_manager()

    class Meta:
        db_table = "league"
        verbose_name = _("League")
        verbose_name_plural = _("Leagues")

    def __str__(self):
        return self.name

    def is_active(self):
        if self.end_dt is not None:
            return self.start_dt <= timezone.now() < self.end_dt
        return self.start_dt <= timezone.now()

    def get_scorer(self):
        return self.rule.get_scorer()


class Score(models.Model):
    league = models.ForeignKey(to=League, on_delete=models.CASCADE, related_name="scores")
    user = models.ForeignKey(to=get_user_model(), on_delete=models.CASCADE, related_name="scores")
    value = models.FloatField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "league")
        db_table = "score"
        verbose_name = _("Score")
        verbose_name_plural = _("Scores")

    def get_scorer(self):
        return self.league.get_scorer()
