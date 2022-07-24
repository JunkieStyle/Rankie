from typing import List
from itertools import groupby

from django.utils import timezone
from django.db.models import Q
from django.contrib.auth import get_user_model

from .models import Game, Score, League, GameResult

User = get_user_model()


def refresh_league_scores(league: League) -> List[Score]:
    """Create or update league's scores."""

    if not league.is_active():
        return list(league.scores.all())

    scorer = league.get_scorer()

    active_league_filter = Q(created__gte=league.start_dt)
    if league.end_dt is not None:
        active_league_filter |= Q(created__lte=league.end_dt)

    results = (
        GameResult.objects.filter(user__in=league.players.all(), game=league.rule.game)
        .filter(active_league_filter)
        .order_by("user")  # TODO: add second ordering ??
    )

    scores_to_update = []
    users_scores = {score.user: score for score in league.scores.all()}
    for user, user_results in groupby(results, lambda x: x.user):
        score = users_scores[user]
        score.value = scorer.score(user_results)
        score.updated = timezone.now()
        scores_to_update.append(score)

    Score.objects.bulk_update(scores_to_update, ["value", "updated"])

    return scores_to_update


def refresh_user_scores(game: Game, user: User) -> List[Score]:
    """Create or update user scores for users' active leagues."""

    results = user.results.filter(game=game)  # TODO: order by ??
    active_leagues = user.leagues.active().filter(rule__game=game)

    scores_to_update = []
    for score in user.scores.filter(league__in=active_leagues):
        scorer = score.get_scorer()
        active_results = filter(lambda x: x.is_active(score.league), results)
        score.value = scorer.score(active_results)
        score.updated = timezone.now()
        scores_to_update.append(score)

    Score.objects.bulk_update(scores_to_update, ["value", "updated"])

    return scores_to_update
