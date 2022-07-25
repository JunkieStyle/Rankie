import re

from abc import ABC, abstractmethod
from pydoc import locate
from collections.abc import Iterable

from apps.rankie.models import Round, League, GameRule, Standing, GameResult, RoundResult


def get_scorer(obj) -> "BaseScorer":
    """Helper function for creating scorer instance."""

    if isinstance(obj, GameRule):
        return locate(obj.py_class)(**obj.py_kwargs)  # noqa
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
    def __init__(self, round_label_re_pattern):
        self.pattern = re.compile(round_label_re_pattern)

    @abstractmethod
    def get_round_score(self, result: GameResult) -> float:
        raise NotImplementedError

    @abstractmethod
    def get_standing_score(self, results: Iterable[RoundResult]) -> float:
        raise NotImplementedError

    def get_round_label(self, result: GameResult) -> int:
        match = self.pattern.search(result.text)
        return match.groups()[0]


class ConstantLinearScorer(BaseScorer):
    """Exists for debugging and test purposes."""

    def __init__(self, round_score=1, round_label_re_pattern=r"^(.*)$"):
        super().__init__(round_label_re_pattern)
        self.round_score = round_score

    def get_round_score(self, result: GameResult) -> float:
        return self.round_score

    def get_standing_score(self, results: Iterable[RoundResult]) -> float:
        return sum(result.score for result in results)
