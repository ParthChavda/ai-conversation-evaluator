from app.confidence.scorer import ConfidenceCalibrator
from app.evaluators.base import BaseEvaluator
from app.models.schemas import ConversationTurn, Facet, FacetEvaluation
from app.services.batch_engine import FacetBatchingEngine
from app.utils.tracing import EvaluationTracer


class EvaluationService:
    def __init__(
        self,
        evaluator: BaseEvaluator,
        batching_engine: FacetBatchingEngine,
        confidence_calibrator: ConfidenceCalibrator,
        tracer: EvaluationTracer,
    ):
        self.evaluator = evaluator
        self.batching_engine = batching_engine
        self.confidence_calibrator = confidence_calibrator
        self.tracer = tracer

    def evaluate_turn(
        self,
        turn: ConversationTurn,
        facets: list[Facet],
        batch_size: int | None = None,
    ) -> tuple[list[FacetEvaluation], int]:
        all_scores: list[FacetEvaluation] = []
        batch_count = 0
        for batch in self.batching_engine.batches(facets, batch_size=batch_size):
            batch_count += 1
            with self.tracer.span(
                "evaluate_facet_batch",
                turn_id=turn.turn_id,
                batch_size=len(batch),
                evaluator=self.evaluator.name,
            ):
                raw_scores = self.evaluator.evaluate_turn(turn, batch)
                all_scores.extend(self.confidence_calibrator.calibrate(raw_scores))
        return all_scores, batch_count
