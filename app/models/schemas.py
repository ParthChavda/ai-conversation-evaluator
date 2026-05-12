from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class EvaluationStrategy(str, Enum):
    rubric = "rubric"
    classifier = "classifier"
    heuristic = "heuristic"
    embedding = "embedding"
    safety = "safety"


class ScoreScale(BaseModel):
    min: float = 0.0
    max: float = 5.0
    step: float = 1.0
    label_min: str | None = None
    label_max: str | None = None


class Facet(BaseModel):
    facet_id: str
    name: str
    category: str
    description: str
    score_scale: ScoreScale = Field(default_factory=ScoreScale)
    evaluation_strategy: EvaluationStrategy = EvaluationStrategy.rubric
    enabled: bool = True
    weight: float = 1.0
    tags: list[str] = Field(default_factory=list)
    prompt_template: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("weight")
    @classmethod
    def weight_must_be_positive(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("facet weight must be positive")
        return value


class ConversationTurn(BaseModel):
    turn_id: str = Field(default_factory=lambda: str(uuid4()))
    role: Literal["user", "assistant", "system"]
    text: str
    timestamp: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Conversation(BaseModel):
    conversation_id: str = Field(default_factory=lambda: str(uuid4()))
    turns: list[ConversationTurn]
    source: str = "api"
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("turns")
    @classmethod
    def require_turns(cls, value: list[ConversationTurn]) -> list[ConversationTurn]:
        if not value:
            raise ValueError("conversation must contain at least one turn")
        return value


class FacetEvaluation(BaseModel):
    facet_id: str
    score: float
    confidence: float
    reasoning_summary: str
    evaluator: str
    strategy: EvaluationStrategy
    metadata: dict[str, Any] = Field(default_factory=dict)


class TurnEvaluation(BaseModel):
    turn_id: str
    role: str
    text: str
    facet_scores: list[FacetEvaluation]
    aggregate_score: float
    aggregate_confidence: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class CategoryMetric(BaseModel):
    category: str
    score: float
    confidence: float
    facets_evaluated: int


class EvaluationMetrics(BaseModel):
    overall_score: float
    overall_confidence: float
    category_scores: list[CategoryMetric]
    total_turns: int
    total_facets: int
    enabled_facets: int
    batches_executed: int


class EvaluationResult(BaseModel):
    evaluation_id: str = Field(default_factory=lambda: str(uuid4()))
    conversation_id: str
    turns: list[TurnEvaluation]
    metrics: EvaluationMetrics
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EvaluateRequest(BaseModel):
    conversation: Conversation
    facet_ids: list[str] | None = None
    categories: list[str] | None = None
    include_disabled: bool = False
    batch_size: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str
    service: str
    evaluator_backend: str
    enabled_facets: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
