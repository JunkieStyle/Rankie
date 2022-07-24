from abc import ABC, abstractmethod
from collections.abc import Iterable

from apps.rankie.models import GameResult


class BaseScorer(ABC):
    @abstractmethod
    def score(self, results) -> float:
        raise NotImplementedError


class DummyScorer(BaseScorer):
    """Exists for debugging and test purposes."""

    def score(self, results: Iterable[GameResult]):
        return sum(1 for _ in results)
