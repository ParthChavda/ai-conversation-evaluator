from collections import defaultdict

from app.models.schemas import CategoryMetric, EvaluationMetrics, Facet, FacetEvaluation, TurnEvaluation


class AggregationService:
    def turn_aggregate(self, evaluations: list[FacetEvaluation], facets_by_id: dict[str, Facet]) -> tuple[float, float]:
        if not evaluations:
            return 0.0, 0.0
        weighted_scores = 0.0
        weighted_confidence = 0.0
        total_weight = 0.0
        for evaluation in evaluations:
            facet = facets_by_id[evaluation.facet_id]
            normalized = _normalize(evaluation.score, facet.score_scale.min, facet.score_scale.max)
            weighted_scores += normalized * facet.weight
            weighted_confidence += evaluation.confidence * facet.weight
            total_weight += facet.weight
        return round(weighted_scores / total_weight, 3), round(weighted_confidence / total_weight, 3)

    def metrics(
        self,
        turn_evaluations: list[TurnEvaluation],
        facets: list[Facet],
        total_batches: int,
    ) -> EvaluationMetrics:
        facets_by_id = {facet.facet_id: facet for facet in facets}
        category_scores: dict[str, list[float]] = defaultdict(list)
        category_confidences: dict[str, list[float]] = defaultdict(list)

        for turn in turn_evaluations:
            for evaluation in turn.facet_scores:
                facet = facets_by_id[evaluation.facet_id]
                category_scores[facet.category].append(
                    _normalize(evaluation.score, facet.score_scale.min, facet.score_scale.max)
                )
                category_confidences[facet.category].append(evaluation.confidence)

        categories = [
            CategoryMetric(
                category=category,
                score=round(sum(scores) / len(scores), 3),
                confidence=round(sum(category_confidences[category]) / len(category_confidences[category]), 3),
                facets_evaluated=len(scores),
            )
            for category, scores in sorted(category_scores.items())
            if scores
        ]

        if turn_evaluations:
            overall_score = sum(turn.aggregate_score for turn in turn_evaluations) / len(turn_evaluations)
            overall_confidence = sum(turn.aggregate_confidence for turn in turn_evaluations) / len(turn_evaluations)
        else:
            overall_score = 0.0
            overall_confidence = 0.0

        return EvaluationMetrics(
            overall_score=round(overall_score, 3),
            overall_confidence=round(overall_confidence, 3),
            category_scores=categories,
            total_turns=len(turn_evaluations),
            total_facets=len(facets),
            enabled_facets=len([facet for facet in facets if facet.enabled]),
            batches_executed=total_batches,
        )


def _normalize(score: float, min_score: float, max_score: float) -> float:
    if max_score == min_score:
        return 0.0
    return max(0.0, min(1.0, (score - min_score) / (max_score - min_score)))
