from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EvaluationJob:
    job_id: str
    payload: dict[str, Any]
    status: str = "queued"


class QueueClient:
    """Redis/Celery-ready queue boundary.

    The synchronous Flask path calls the pipeline directly today. Distributed
    inference can replace this class with a Redis Stream, Celery, RQ, or Kafka
    producer while preserving request and result schemas.
    """

    def enqueue(self, payload: dict[str, Any]) -> EvaluationJob:
        raise NotImplementedError("queue backend is not configured")
