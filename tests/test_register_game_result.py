from datetime import timedelta

from django.utils import timezone
from model_bakery import baker

from apps.rankie.core import register_game_result, get_league_queryset_for_standings_update
from apps.rankie.models import Game, Round, League, GameRule, GameResult, RoundResult


def test_get_league_queryset_for_standings_update(django_user_model, db, django_assert_max_num_queries):
    user = baker.make(django_user_model)
    another_user = baker.make(django_user_model)
    game = baker.make(Game)

    rule = baker.make(GameRule, game=game, py_class="apps.rankie.scorers.ConstantLinearScorer")
    leagues = baker.make(League, rule=rule, start_dt=(timezone.now() - timedelta(days=1)), _quantity=2)
    for league in leagues:
        league.players.add(user)
        league.players.add(another_user)
        league.save()
        rounds = baker.make(Round, league=league, _quantity=5)
        for round in rounds:
            baker.make(RoundResult, round=round, player=user)
            baker.make(RoundResult, round=round, player=another_user)

    with django_assert_max_num_queries(5):
        active_leagues = get_league_queryset_for_standings_update(user, game)
        assert len(active_leagues) == 2
        for league in active_leagues:
            assert len(league.fetched_rounds) == 5
            for round in league.fetched_rounds:
                assert len(round.fetched_round_results) == 2


def test_register_games(db, django_user_model):
    user = baker.make(django_user_model)
    game = baker.make(Game)
    rule = baker.make(GameRule, game=game, py_class="apps.rankie.scorers.ConstantLinearScorer")
    league = baker.make(League, rule=rule, start_dt=(timezone.now() - timedelta(days=1)), players=[user])
    game_result = baker.make(GameResult, player=user, game=game)

    assert Round.objects.filter(league=league).count() == 0
    assert RoundResult.objects.filter(player=user).count() == 0

    register_game_result(game_result)

    assert Round.objects.filter(league=league).count() == 1
    assert RoundResult.objects.filter(player=user).count() == 1
