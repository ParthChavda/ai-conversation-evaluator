from app.facets.registry import FacetRegistry
from app.models.schemas import EvaluateRequest, EvaluationResult, TurnEvaluation
from app.services.aggregation_service import AggregationService
from app.services.evaluation_service import EvaluationService
from app.services.storage import InMemoryEvaluationStore


class ConversationEvaluationPipeline:
    def __init__(
        self,
        facet_registry: FacetRegistry,
        evaluation_service: EvaluationService,
        aggregation_service: AggregationService,
        store: InMemoryEvaluationStore,
    ):
        self.facet_registry = facet_registry
        self.evaluation_service = evaluation_service
        self.aggregation_service = aggregation_service
        self.store = store

    def run(self, request: EvaluateRequest) -> EvaluationResult:
        facets = self.facet_registry.filter(
            facet_ids=request.facet_ids,
            categories=request.categories,
            include_disabled=request.include_disabled,
        )
        facets_by_id = {facet.facet_id: facet for facet in facets}
        turn_results: list[TurnEvaluation] = []
        total_batches = 0

        for turn in request.conversation.turns:
            facet_scores, batch_count = self.evaluation_service.evaluate_turn(
                turn,
                facets,
                batch_size=request.batch_size,
            )
            total_batches += batch_count
            score, confidence = self.aggregation_service.turn_aggregate(
                facet_scores, facets_by_id
            )
            turn_results.append(
                TurnEvaluation(
                    turn_id=turn.turn_id,
                    role=turn.role,
                    text=turn.text,
                    facet_scores=facet_scores,
                    aggregate_score=score,
                    aggregate_confidence=confidence,
                    metadata=turn.metadata,
                )
            )

        metrics = self.aggregation_service.metrics(turn_results, facets, total_batches)
        result = EvaluationResult(
            conversation_id=request.conversation.conversation_id,
            turns=turn_results,
            metrics=metrics,
            metadata={
                "facet_filter": {
                    "facet_ids": request.facet_ids,
                    "categories": request.categories,
                    "include_disabled": request.include_disabled,
                },
                **request.metadata,
            },
        )
        self.store.save(request.conversation, result)
        return result
