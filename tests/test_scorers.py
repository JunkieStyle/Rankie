import pytest

from model_bakery import baker

from apps.rankie.models import Game, GameRule, GameResult
from apps.rankie.scorers import get_scorer


@pytest.fixture
def wordle_eng_game(db):
    return baker.make(Game, label="wordle_eng", parser_regex=r"(?P<game>\w+) (?P<round>[0-9]+) (?P<score>[\s\S]*)")


@pytest.fixture
def wordle_ru_game(db):
    return baker.make(
        Game,
        label="wordle_ru",
        parser_regex=r"Игра (?P<game>[ A-zА-я\)\(]+) День #(?P<round>[0-9]+) (?P<score>[\s\S]*)",
    )


@pytest.fixture
def reversle_eng_game(db):
    return baker.make(Game, label="reversle_eng", parser_regex=r"(?P<game>\w+) #(?P<round>[0-9]+) (?P<score>[\s\S]*)")


class TestWordleEngScorers:
    def test_simple_scorer__default(self, db, wordle_eng_game):
        result_text = """
            Wordle 409 X/6
            ⬛️⬛️⬛️⬛️⬛️
            ⬛️🟩⬛️⬛️⬛️
            🟨🟩⬛️⬛️⬛️
            ⬛️🟩⬛️🟩🟩
            ⬛️🟩⬛️🟩🟩
            ⬛️🟩⬛️🟩🟩
        """
        rule = baker.make(GameRule, game=wordle_eng_game, py_class="apps.rankie.scorers.SimpleScorer")
        result = baker.make(GameResult, game=wordle_eng_game, text=result_text)
        scorer = get_scorer(rule)
        assert scorer.get_game_label(result) == "Wordle"
        assert scorer.get_round_label(result) == "409"
        assert scorer.get_round_score(result) == 1

    @pytest.mark.parametrize(
        "result_text, expression, expected_round_score",
        [
            ("Wordle 409 1/6", "{total} / {value}", 6),
            ("Wordle 409 2/6", "{total} / {value}", 3),
            ("Wordle 409 3/6", "{total} / {value}", 2),
            ("Wordle 409 4/6", "{total} / {value}", 1.5),
            ("Wordle 409 5/6", "{total} / {value}", 1.2),
            ("Wordle 409 6/6", "{total} / {value}", 1),
            ("Wordle 409 X/6", "{total} / {value}", 0),
        ],
    )
    def test_expression_scorer(self, db, result_text, expression, expected_round_score, wordle_eng_game):
        rule = baker.make(
            GameRule,
            game=wordle_eng_game,
            py_class="apps.rankie.scorers.ExpressionScorer",
            py_kwargs={"vars_regex": "(?P<value>[0-9X]+)/(?P<total>[0-9]+)", "expression": expression},
        )
        result = baker.make(GameResult, game=wordle_eng_game, text=result_text)
        scorer = get_scorer(rule)
        assert scorer.get_game_label(result) == "Wordle"
        assert scorer.get_round_label(result) == "409"
        assert scorer.get_round_score(result) == expected_round_score


class TestWordleRuScorers:
    def test_simple_scorer__default(self, db, wordle_ru_game):
        result_text = """
            Игра Wordle (RU) День #208 5/6
            🟩⬜️⬜️⬜️⬜️
            🟩🟩⬜️⬜️⬜️
            🟩🟩⬜️⬜️🟩
            🟩🟩🟩⬜️🟩
            🟩🟩🟩🟩🟩
            #вордли
            Отгадайте слово на  https://wordle.belousov.one/
        """
        rule = baker.make(GameRule, game=wordle_ru_game, py_class="apps.rankie.scorers.SimpleScorer")
        result = baker.make(GameResult, game=wordle_ru_game, text=result_text)
        scorer = get_scorer(rule)
        assert scorer.get_game_label(result) == "Wordle (RU)"
        assert scorer.get_round_label(result) == "208"
        assert scorer.get_round_score(result) == 1

    @pytest.mark.parametrize(
        "result_text, expression, expected_round_score",
        [
            ("Игра Wordle (RU) День #208 1/6", "{total} / {value}", 6),
            ("Игра Wordle (RU) День #208 2/6", "{total} / {value}", 3),
            ("Игра Wordle (RU) День #208 3/6", "{total} / {value}", 2),
            ("Игра Wordle (RU) День #208 4/6", "{total} / {value}", 1.5),
            ("Игра Wordle (RU) День #208 5/6", "{total} / {value}", 1.2),
            ("Игра Wordle (RU) День #208 6/6", "{total} / {value}", 1),
            ("Игра Wordle (RU) День #208 X/6", "{total} / {value}", 0),
        ],
    )
    def test_expression_scorer(self, db, result_text, expression, expected_round_score, wordle_ru_game):
        rule = baker.make(
            GameRule,
            game=wordle_ru_game,
            py_class="apps.rankie.scorers.ExpressionScorer",
            py_kwargs={"vars_regex": "(?P<value>[0-9X]+)/(?P<total>[0-9]+)", "expression": expression},
        )
        result = baker.make(GameResult, game=wordle_ru_game, text=result_text)
        scorer = get_scorer(rule)
        assert scorer.get_game_label(result) == "Wordle (RU)"
        assert scorer.get_round_label(result) == "208"
        assert scorer.get_round_score(result) == expected_round_score


class TestReversleEngScorers:
    def test_simple_scorer__default(self, db, reversle_eng_game):
        result_text = """
            Reversle #169 82.32s

            🟨🟨⬜️⬜️⬜️ 8.60s
            ⬜️🟨⬜️⬜️🟨 52.20s
            🟨⬜️⬜️🟩🟩 11.21s
            ⬜️⬜️⬜️🟨⬜️ 10.31s
            🟩🟩🟩🟩🟩

            reversle.net
        """
        rule = baker.make(GameRule, game=reversle_eng_game, py_class="apps.rankie.scorers.SimpleScorer")
        result = baker.make(GameResult, game=reversle_eng_game, text=result_text)
        scorer = get_scorer(rule)
        assert scorer.get_game_label(result) == "Reversle"
        assert scorer.get_round_label(result) == "169"
        assert scorer.get_round_score(result) == 1

    @pytest.mark.parametrize(
        "result_text, expression, expected_round_score",
        [
            ("Reversle #169 60.00s", "300 / {value}", 5),
            ("Reversle #169 500s", "300 / {value}", 0.6),
            ("Reversle #169 0s", "300 / {value}", 0),
        ],
    )
    def test_expression_scorer(self, db, result_text, expression, expected_round_score, reversle_eng_game):
        rule = baker.make(
            GameRule,
            game=reversle_eng_game,
            py_class="apps.rankie.scorers.ExpressionScorer",
            py_kwargs={"vars_regex": "(?P<value>[0-9.]+)s", "expression": expression},
        )
        result = baker.make(GameResult, game=reversle_eng_game, text=result_text)
        scorer = get_scorer(rule)
        assert scorer.get_game_label(result) == "Reversle"
        assert scorer.get_round_label(result) == "169"
        assert scorer.get_round_score(result) == expected_round_score
