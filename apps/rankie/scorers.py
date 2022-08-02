import re
import ast
import operator as op

from abc import ABC, abstractmethod
from pydoc import locate
from typing import Dict, Callable
from collections.abc import Iterable

from apps.rankie.models import Game, Round, League, GameRule, Standing, GameResult, RoundResult


def get_scorer(obj) -> "BaseScorer":
    """Helper function for creating scorer instance."""

    if isinstance(obj, GameRule):
        parser_regex = obj.py_kwargs.pop("parser_regex", obj.game.parser_regex)
        return locate(obj.py_class)(parser_regex=parser_regex, **obj.py_kwargs)  # noqa
    elif isinstance(obj, League):
        return get_scorer(obj.rule)
    elif isinstance(obj, Round):
        return get_scorer(obj.league.rule)
    elif isinstance(obj, RoundResult):
        return get_scorer(obj.round.league.rule)
    elif isinstance(obj, Standing):
        return get_scorer(obj.league.rule)
    else:
        raise TypeError(f"Object of type {type(obj)} is not supported")


class BaseScorer(ABC):
    def __init__(self, parser_regex: str, aggregator: Callable[[Iterable[float]], float] = sum):
        self.pattern = re.compile(parser_regex)
        self.aggregator = aggregator

    def parse_game_result(self, result: GameResult):
        match = self.pattern.search(result.text)
        groups = match.groupdict()
        for group in Game.RE_GROUPS:
            if group not in groups:
                raise KeyError(f"Missing group '{group}' from parsed game result with")
        return groups

    def get_standing_score(self, results: Iterable[RoundResult]) -> float:
        return self.aggregator(result.score for result in results)

    def get_round_label(self, result: GameResult) -> float:
        return self.parse_game_result(result)[Game.RE_ROUND_GROUP]

    def get_game_label(self, result: GameResult) -> str:
        return self.parse_game_result(result)[Game.RE_GAME_GROUP]

    @abstractmethod
    def get_round_score(self, result: GameResult) -> float:
        raise NotImplementedError


class SimpleScorer(BaseScorer):
    """Exists for debugging and test purposes."""

    def get_round_score(self, result: GameResult) -> float:
        return 1


class ExpressionScorer(BaseScorer):
    # supported operators
    OPERATORS: Dict[type(ast.operator), Callable] = {
        ast.Add: op.add,
        ast.Sub: op.sub,
        ast.Mult: op.mul,
        ast.Div: op.truediv,
        ast.Pow: op.pow,
        ast.USub: op.neg,
    }

    def __init__(self, vars_regex, expression: str, not_numeric_default: float = 0, **kwargs):
        super().__init__(**kwargs)
        self.vars_regex_pattern = re.compile(vars_regex)
        self.expression = expression
        self.not_numeric_default = not_numeric_default

    def get_round_score(self, result: GameResult) -> float:
        raw_score = self.parse_game_result(result)[Game.RE_SCORE_GROUP]
        variables = self.vars_regex_pattern.search(raw_score).groupdict()
        variables = {
            k: float(v) if v.replace(".", "", 1).isdigit() else self.not_numeric_default for k, v in variables.items()
        }
        expression = self.expression.format(**variables)
        try:
            return self._eval_expr(expression)
        except ZeroDivisionError:
            return self.not_numeric_default

    def _eval_expr(self, expr):
        return self.eval_(ast.parse(expr, mode="eval").body)

    def eval_(self, node):
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            return self.OPERATORS[type(node.op)](self.eval_(node.left), self.eval_(node.right))
        elif isinstance(node, ast.UnaryOp):
            return self.OPERATORS[type(node.op)](self.eval_(node.operand))
        else:
            raise TypeError(node)
