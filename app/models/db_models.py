from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ConversationRecord:
    conversation_id: str
    source: str
    metadata: dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class TurnRecord:
    turn_id: str
    conversation_id: str
    role: str
    text: str
    ordinal: int
    metadata: dict[str, Any]


@dataclass
class FacetRecord:
    facet_id: str
    name: str
    category: str
    strategy: str
    enabled: bool
    weight: float
    definition: dict[str, Any]


@dataclass
class EvaluationRecord:
    evaluation_id: str
    conversation_id: str
    turn_id: str
    facet_id: str
    score: float
    confidence: float
    reasoning_summary: str
    evaluator: str
    metadata: dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class MetricRecord:
    evaluation_id: str
    metric_name: str
    metric_value: float
    dimensions: dict[str, Any]
