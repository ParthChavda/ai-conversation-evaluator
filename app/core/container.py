from dataclasses import dataclass

from app.confidence.scorer import ConfidenceCalibrator
from app.core.config import Settings
from app.evaluators.factory import EvaluatorFactory
from app.facets.registry import FacetRegistry
from app.pipelines.conversation_pipeline import ConversationEvaluationPipeline
from app.services.aggregation_service import AggregationService
from app.services.batch_engine import FacetBatchingEngine
from app.services.evaluation_service import EvaluationService
from app.services.sqlalchemy_storage import SQLAlchemyEvaluationStore
from app.services.storage import InMemoryEvaluationStore
from app.utils.tracing import EvaluationTracer


@dataclass(frozen=True)
class Container:
    settings: Settings
    facet_registry: FacetRegistry
    evaluation_service: EvaluationService
    store: InMemoryEvaluationStore | SQLAlchemyEvaluationStore
    pipeline: ConversationEvaluationPipeline


def build_container(settings: Settings) -> Container:
    registry = FacetRegistry.from_file(settings.resolved_facet_config_path)
    evaluator = EvaluatorFactory(settings).create(settings.evaluator_backend)
    batching = FacetBatchingEngine(batch_size=settings.facet_batch_size)
    calibrator = ConfidenceCalibrator()
    tracer = EvaluationTracer(enabled=settings.trace_enabled)
    if settings.storage_backend == "memory":
        store = InMemoryEvaluationStore()
    else:
        store = SQLAlchemyEvaluationStore(settings.resolved_database_url)
        store.sync_facets(registry.all(include_disabled=True))
    aggregation = AggregationService()
    service = EvaluationService(
        evaluator=evaluator,
        batching_engine=batching,
        confidence_calibrator=calibrator,
        tracer=tracer,
    )
    pipeline = ConversationEvaluationPipeline(
        facet_registry=registry,
        evaluation_service=service,
        aggregation_service=aggregation,
        store=store,
    )
    return Container(
        settings=settings,
        facet_registry=registry,
        evaluation_service=service,
        store=store,
        pipeline=pipeline,
    )
