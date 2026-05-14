from typing import Any


class ExperimentTracker:
    """Placeholder for MLflow, Weights & Biases, or internal benchmark stores."""

    def log_metric(
        self, name: str, value: float, dimensions: dict[str, Any] | None = None
    ) -> None:
        return None

    def log_artifact(self, name: str, payload: dict[str, Any]) -> None:
        return None
