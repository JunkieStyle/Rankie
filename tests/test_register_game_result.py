from datetime import timedelta

import pytest

from django.utils import timezone
from model_bakery import baker

from apps.rankie.core import register_game_result, get_league_queryset_for_standings_update
from apps.rankie.models import Game, Round, League, GameRule, Standing, GameResult, RoundResult


@pytest.fixture
def league(db):
    game = baker.make(Game)
    rule = baker.make(GameRule, game=game, py_class="apps.rankie.scorers.ConstantLinearScorer")
    league = baker.make(League, rule=rule, start_dt=(timezone.now() - timedelta(days=1)))
    return league


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


def test_standing_on_adding_player(db, django_user_model, league):
    player = baker.make(django_user_model)
    assert not Standing.objects.filter(player=player, league=league).exist()

    league.players.add(player)
    league.save()
    standing = Standing.objects.filter(player=player, league=league).last()
    assert standing is not None
    assert Standing.objects.count() == 1
    assert standing.score is None
    assert standing.rank is None
    assert standing.mvp_count == 0


def test_register_single_player_single_result(db, django_user_model, league):
    game = league.rule.game
    player = baker.make(django_user_model)
    league.players.add(player)
    league.save()

    round_label = "label"
    game_result = baker.make(GameResult, player=player, game=game, text=round_label)

    # no registered result
    assert Round.objects.filter(league=league).count() == 0
    assert RoundResult.objects.filter(player=player).count() == 0

    register_game_result(game_result)

    # test created round
    assert Round.objects.filter(league=league, label=round_label).count() == 1
    round = Round.objects.get(league=league, label=round_label)
    assert round.mvp == player

    # test created round result
    expected_score = 1
    assert RoundResult.objects.filter(player=player, round=round).count() == 1
    round_result = RoundResult.objects.get(player=player, round=round)
    assert round_result.score == expected_score
    assert round_result.raw == game_result

    # test updated standing
    standing = Standing.objects.get(player=player, league=league)
    assert standing.score == expected_score
    assert standing.mvp_count == 1


def test_register_single_player_multi_results(db, django_user_model, league):
    player = baker.make(django_user_model)
    league.players.add(player)
    league.save()

    round_label1 = ("1",)
    game_result1 = baker.make(GameResult, player=player, game=league.game, text=round_label1)
    register_game_result(game_result1)

    round_label2 = ("2",)
    game_result2 = baker.make(GameResult, player=player, game=league.game, text=round_label2)
    register_game_result(game_result2)

    standing = Standing.objects.get(player=player, league=league)
    assert standing.score == RoundResult.objects.filter(player=player, round__league=league).sum()
    assert standing.mvp_count == 2


def test_register_multi_player_single_results(db, django_user_model, league):
    player1 = baker.make(django_user_model)
    player2 = baker.make(django_user_model)
    league.players.set([player1, player2])
    league.save()

    round_label = "1"
    game_result1 = baker.make(GameResult, player=player1, game=league.rule.game, text=round_label)
    game_result2 = baker.make(GameResult, player=player2, game=league.rule.game, text=round_label)

    register_game_result(game_result1)
    register_game_result(game_result2)

    round = Round.objects.get(league=league, label=round_label)
    assert round.mvp == player1

    standing1 = Standing.objects.get(player=player1, league=league)
    standing2 = Standing.objects.get(player=player2, league=league)
    assert standing1.mvp_count == 1
    assert standing2.mvp_count == 0


def test_register_multi_player_multi_results(db, django_user_model, league):

    players = [baker.make(django_user_model, id=i) for i in range(0, 4)]
    league.players.add(*players)

    round_labels = [str(i) for i in range(0, 3)]
    game_results = [
        [baker.make(GameResult, player=player, game=league.rule.game, text=round_label) for player in players]
        for round_label in round_labels
    ]

    # Register round 0
    for game_result in game_results[0]:
        register_game_result(game_result)
    data = Standing.objects.filter(league=league).order_by("rank").values("rank", "player", "score", "mvp_count")
    assert list(data) == [
        {"rank": 1, "player": 0, "score": 1.0, "mvp_count": 1},
        {"rank": 2, "player": 1, "score": 1.0, "mvp_count": 0},
        {"rank": 3, "player": 2, "score": 1.0, "mvp_count": 0},
        {"rank": 4, "player": 3, "score": 1.0, "mvp_count": 0},
    ]

    # Register round 1
    for game_result in game_results[1]:
        register_game_result(game_result)
    data = Standing.objects.filter(league=league).order_by("rank").values("rank", "player", "score", "mvp_count")
    assert list(data) == [
        {"rank": 1, "player": 0, "score": 2.0, "mvp_count": 2},
        {"rank": 2, "player": 1, "score": 2.0, "mvp_count": 0},
        {"rank": 3, "player": 2, "score": 2.0, "mvp_count": 0},
        {"rank": 4, "player": 3, "score": 2.0, "mvp_count": 0},
    ]

    # Register round 2 only for player 3
    register_game_result(game_results[2][3])
    data = Standing.objects.filter(league=league).order_by("rank").values("rank", "player", "score", "mvp_count")
    assert list(data) == [
        {"rank": 1, "player": 3, "score": 3.0, "mvp_count": 1},
        {"rank": 2, "player": 0, "score": 2.0, "mvp_count": 2},
        {"rank": 3, "player": 1, "score": 2.0, "mvp_count": 0},
        {"rank": 4, "player": 2, "score": 2.0, "mvp_count": 0},
    ]

    # Lower player 3 round 2 score manually
    standing3 = Standing.objects.get(league=league, player=players[3])
    standing3.score -= 0.5
    standing3.save()
    round_result33 = RoundResult.objects.get(round__label=round_labels[2], player=players[3])
    round_result33.score -= 0.5
    round_result33.save()

    # Register round 2 only for player 1
    register_game_result(game_results[2][1])
    data = Standing.objects.filter(league=league).order_by("rank").values("rank", "player", "score", "mvp_count")
    assert list(data) == [
        {"rank": 1, "player": 1, "score": 3.0, "mvp_count": 1},
        {"rank": 2, "player": 3, "score": 2.5, "mvp_count": 0},
        {"rank": 3, "player": 0, "score": 2.0, "mvp_count": 2},
        {"rank": 4, "player": 2, "score": 2.0, "mvp_count": 0},
    ]
