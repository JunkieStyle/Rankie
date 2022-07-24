from datetime import timedelta

from django.utils import timezone
from model_bakery import baker

from apps.rankie.core import refresh_user_scores, refresh_league_scores
from apps.rankie.models import Game, League, GameRule, GameResult


def test_refresh_user_scores(db, django_user_model):
    user = baker.make(django_user_model)
    game = baker.make(Game)
    results = baker.make(GameResult, user=user, game=game, _quantity=2)
    rule = baker.make(GameRule, game=game, python_class="apps.rankie.scorers.DummyScorer")
    league = baker.make(League, rule=rule, start_dt=(timezone.now() - timedelta(days=1)))
    league.players.add(user)
    league.save()

    refresh_user_scores(game, user)
    score = user.scores.get(league=league)
    assert score.value == len(results)
    assert score.updated > score.created


def test_refresh_league_scores(db, django_user_model):
    user = baker.make(django_user_model)
    game = baker.make(Game)
    results = baker.make(GameResult, user=user, game=game, _quantity=5)
    rule = baker.make(GameRule, game=game, python_class="apps.rankie.scorers.DummyScorer")
    league = baker.make(League, rule=rule, start_dt=(timezone.now() - timedelta(days=1)))
    league.players.add(user)
    league.save()

    refresh_league_scores(league)
    score = league.scores.get(user=user)
    assert score.value == len(results)
    assert score.updated > score.created
