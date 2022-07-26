import re

from django.db import models
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _

User = get_user_model()


@deconstructible
class GameParserValidator:
    def __init__(self, required_groups=None):
        self.required_groups = required_groups if required_groups else []

    def __call__(self, value):
        self.validate_is_regex(value)
        self.validate_regex_groups(value)

    @staticmethod
    def validate_is_regex(value):
        try:
            re.compile(value)
        except Exception:
            raise ValidationError(
                _("%(value)s is not a valid regular expression"),
                params={"value": value},
            )

    def validate_regex_groups(self, value):
        pattern = re.compile(value)
        for group in self.required_groups:
            if group not in pattern.groupindex:
                raise ValidationError(
                    _('%(value)s doesnt contain required group named "${group}"'),
                    params={"value": value, "group": group},
                )


class Game(models.Model):
    RE_GAME_GROUP = "game"
    RE_ROUND_GROUP = "round"
    RE_SCORE_GROUP = "score"
    RE_GROUPS = [RE_GAME_GROUP, RE_ROUND_GROUP, RE_SCORE_GROUP]

    label = models.SlugField(max_length=32, unique=True)
    name = models.CharField(max_length=128, unique=True)
    url = models.URLField()
    parser_regex = models.TextField(validators=[GameParserValidator(RE_GROUPS)])
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
    py_kwargs = models.JSONField(default=dict, null=True, blank=True)
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
        return f"{self.player}'s {self.game} result"


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
    public = models.BooleanField(default=False)
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
        return f"Round {self.label} of {self.league}"


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
        return f"{self.player}'s round {self.round} result"


class LeagueEvent(models.Model):
    # noinspection PyPep8Naming
    class EV_TYPE(models.TextChoices):  # noqa: N801
        NEW_LEADER = "NEW_LEADER"
        NEW_SCORE = "NEW_SCORE"
        NEW_PLAYER = "NEW_PLAYER"
        NEW_MVP = "NEW_MVP"
        PLAYER_LEFT = "PLAYER_LEFT"
        LEAGUE_FINISHED = "LEAGUE_FINISHED"

    league = models.ForeignKey(to=League, on_delete=models.CASCADE)
    ev_type = models.CharField(max_length=32, choices=EV_TYPE.choices)
    context = models.JSONField(default=dict)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "league_event"
        verbose_name = _("League event")
        verbose_name_plural = _("League events")
        default_related_name = "events"


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
        return f"{self.player}'s standing in league {self.league}"
