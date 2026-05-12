import json

from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session, sessionmaker

from app.models.orm import (
    Base,
    ConversationORM,
    EvaluationResultORM,
    FacetEvaluationORM,
    FacetORM,
    MetricORM,
    TurnORM,
)
from app.models.schemas import Conversation, EvaluationResult, Facet


class SQLAlchemyEvaluationStore:
    def __init__(self, database_url: str):
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        self.engine = create_engine(database_url, future=True, connect_args=connect_args)
        self.session_factory = sessionmaker(self.engine, expire_on_commit=False, future=True)
        Base.metadata.create_all(self.engine)

    def sync_facets(self, facets: list[Facet]) -> None:
        with self.session_factory() as session, session.begin():
            for facet in facets:
                session.merge(
                    FacetORM(
                        facet_id=facet.facet_id,
                        name=facet.name,
                        category=facet.category,
                        strategy=facet.evaluation_strategy.value,
                        enabled=facet.enabled,
                        weight=facet.weight,
                        definition_json=facet.model_dump_json(),
                    )
                )

    def save(self, conversation: Conversation, result: EvaluationResult) -> None:
        with self.session_factory() as session, session.begin():
            self._save_conversation(session, conversation)
            self._save_result(session, result)

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        with self.session_factory() as session:
            record = session.get(ConversationORM, conversation_id)
            if record is None:
                return None
            return Conversation.model_validate(json.loads(record.payload_json))

    def get_result(self, conversation_id: str) -> EvaluationResult | None:
        with self.session_factory() as session:
            record = session.execute(
                select(EvaluationResultORM)
                .where(EvaluationResultORM.conversation_id == conversation_id)
                .order_by(EvaluationResultORM.created_at.desc())
                .limit(1)
            ).scalar_one_or_none()
            if record is None:
                return None
            return EvaluationResult.model_validate(json.loads(record.payload_json))

    def _save_conversation(self, session: Session, conversation: Conversation) -> None:
        session.execute(delete(TurnORM).where(TurnORM.conversation_id == conversation.conversation_id))
        session.merge(
            ConversationORM(
                conversation_id=conversation.conversation_id,
                source=conversation.source,
                payload_json=conversation.model_dump_json(),
                metadata_json=json.dumps(conversation.metadata),
                created_at=conversation.created_at,
            )
        )
        for ordinal, turn in enumerate(conversation.turns):
            session.merge(
                TurnORM(
                    turn_id=turn.turn_id,
                    conversation_id=conversation.conversation_id,
                    role=turn.role,
                    text=turn.text,
                    ordinal=ordinal,
                    metadata_json=json.dumps(turn.metadata),
                )
            )

    def _save_result(self, session: Session, result: EvaluationResult) -> None:
        session.merge(
            EvaluationResultORM(
                evaluation_id=result.evaluation_id,
                conversation_id=result.conversation_id,
                payload_json=result.model_dump_json(),
                created_at=result.created_at,
            )
        )
        session.execute(delete(FacetEvaluationORM).where(FacetEvaluationORM.evaluation_id == result.evaluation_id))
        session.execute(delete(MetricORM).where(MetricORM.evaluation_id == result.evaluation_id))

        for turn in result.turns:
            for evaluation in turn.facet_scores:
                session.add(
                    FacetEvaluationORM(
                        evaluation_id=result.evaluation_id,
                        conversation_id=result.conversation_id,
                        turn_id=turn.turn_id,
                        facet_id=evaluation.facet_id,
                        score=evaluation.score,
                        confidence=evaluation.confidence,
                        reasoning_summary=evaluation.reasoning_summary,
                        evaluator=evaluation.evaluator,
                        metadata_json=json.dumps(evaluation.metadata),
                    )
                )

        session.add_all(
            [
                MetricORM(
                    evaluation_id=result.evaluation_id,
                    metric_name="overall_score",
                    metric_value=result.metrics.overall_score,
                    dimensions_json=json.dumps({}),
                ),
                MetricORM(
                    evaluation_id=result.evaluation_id,
                    metric_name="overall_confidence",
                    metric_value=result.metrics.overall_confidence,
                    dimensions_json=json.dumps({}),
                ),
            ]
        )
        for category in result.metrics.category_scores:
            session.add(
                MetricORM(
                    evaluation_id=result.evaluation_id,
                    metric_name="category_score",
                    metric_value=category.score,
                    dimensions_json=json.dumps(
                        {
                            "category": category.category,
                            "confidence": category.confidence,
                            "facets_evaluated": category.facets_evaluated,
                        }
                    ),
                )
            )
