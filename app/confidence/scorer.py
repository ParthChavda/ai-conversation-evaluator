from app.models.schemas import FacetEvaluation


class ConfidenceCalibrator:
    """Calibration hook for evaluator-specific confidence normalization."""

    def calibrate(self, evaluations: list[FacetEvaluation]) -> list[FacetEvaluation]:
        calibrated: list[FacetEvaluation] = []
        for evaluation in evaluations:
            confidence = max(0.0, min(1.0, evaluation.confidence))
            calibrated.append(evaluation.model_copy(update={"confidence": round(confidence, 3)}))
        return calibrated
