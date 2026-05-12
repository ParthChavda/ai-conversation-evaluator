# Architecture

The framework is a schema-first Flask evaluation service built around replaceable service boundaries.

## Flow

1. `FacetRegistry` loads JSON or YAML facet definitions at startup.
2. `ConversationEvaluationPipeline` selects enabled facets by id/category.
3. `FacetBatchingEngine` chunks facets so a 300-facet or 5000-facet run uses the same code path.
4. `EvaluationService` sends one turn and one facet batch to the active evaluator.
5. `ConfidenceCalibrator` normalizes confidence values from evaluator-specific formats.
6. `AggregationService` computes weighted turn, category, and conversation metrics.
7. `SQLAlchemyEvaluationStore` persists conversations, turns, facets, evaluation rows, and metrics to SQLite by default. The same repository boundary can point at Postgres in production.

## Scaling To 5000+ Facets

The system avoids hardcoded facets and monolithic prompts. Facets are independent records with strategy and scale metadata, and the batch engine controls inference payload size. Future distributed inference can shard by conversation, turn, facet category, or facet batch.

Recommended production path:

- Use Postgres for conversations, turns, facets, evaluations, and metrics by setting `ACE_DATABASE_URL`.
- Use Redis/Celery, RQ, or Kafka for async evaluation jobs.
- Cache model weights per worker using `ModelCache` or serving infrastructure such as vLLM/TGI.
- Split large registries by category and strategy, then route safety/classifier/embedding/rubric facets to specialized evaluators.
- Persist trace logs and timing metrics to OpenTelemetry-compatible infrastructure.

## Evaluator Plugins

`BaseEvaluator` defines the evaluator contract. The included mock evaluator is deterministic and testable. Qwen, Llama, and Mixtral-compatible backends use the transformers adapter, which builds one prompt per facet batch, generates strict JSON, validates score/confidence bounds, and falls back safely when model output is malformed.
