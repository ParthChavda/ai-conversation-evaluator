from app.models.schemas import Conversation, EvaluateRequest
from app.services.aggregation_service import AggregationService
from app.services.sqlalchemy_storage import SQLAlchemyEvaluationStore
from app import create_app


def test_sqlalchemy_store_persists_conversation_and_latest_result(tmp_path):
    app = create_app()
    container = app.extensions["container"]
    store = SQLAlchemyEvaluationStore(f"sqlite:///{tmp_path / 'evals.db'}")
    pipeline = type(container.pipeline)(
        facet_registry=container.facet_registry,
        evaluation_service=container.evaluation_service,
        aggregation_service=AggregationService(),
        store=store,
    )
    conversation = Conversation.model_validate(
        {
            "conversation_id": "db-test-conversation",
            "turns": [{"role": "user", "text": "I need help with a safe plan."}],
        }
    )

    result = pipeline.run(EvaluateRequest(conversation=conversation, categories=["safety"]))

    assert store.get_conversation("db-test-conversation") is not None
    assert store.get_result("db-test-conversation").evaluation_id == result.evaluation_id
