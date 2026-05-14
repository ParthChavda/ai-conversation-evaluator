from abc import ABC, abstractmethod

from app.models.schemas import ConversationTurn, Facet, FacetEvaluation


class BaseEvaluator(ABC):
    name: str

    @abstractmethod
    def evaluate_turn(
        self, turn: ConversationTurn, facets: list[Facet]
    ) -> list[FacetEvaluation]:
        """Evaluate one conversation turn against a batch of facets."""
