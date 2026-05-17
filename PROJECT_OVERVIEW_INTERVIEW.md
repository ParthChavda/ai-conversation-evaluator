# AI Conversation Evaluator - Project Overview For Interviews

## 1. One-Line Summary

AI Conversation Evaluator is a Flask-based evaluation service that scores each conversation turn across hundreds of configurable behavioral, safety, emotional, pragmatic, and quality facets using an open-weight Qwen model, then returns per-facet scores, confidence, reasoning, and aggregate metrics.

## 2. Simple Interview Explanation

This project was built for the Ocean Across AI/ML Engineer assignment. The main idea is to avoid hardcoding evaluation criteria in code. Instead, the system converts a facet dataset into a JSON registry, loads those facets dynamically, batches them, evaluates each conversation turn with an LLM, calibrates confidence, aggregates weighted scores, and stores results in SQLite.

In simple terms:

1. User sends a conversation to the API.
2. App selects enabled facets from `configs/facets.assignment.json`.
3. Facets are split into batches to control LLM prompt size.
4. Qwen evaluates each turn against each facet.
5. The app validates and clamps model output.
6. Scores are normalized and aggregated by turn, category, and whole conversation.
7. Full results are saved in SQLite and returned through the API.

## 3. What Problem It Solves

Manual conversation evaluation does not scale when there are hundreds of dimensions like safety, emotion, pragmatics, personality traits, linguistic quality, and technical skill. This project creates a reusable benchmark framework where evaluation dimensions are data-driven and can grow without rewriting the pipeline.

The current registry contains **399 facets** from `data/facets_assignment.csv`, grouped into:

- `personality_and_behavior`: 318 facets
- `pragmatics`: 19 facets
- `culture_and_values`: 18 facets
- `emotion`: 16 facets
- `technical_skill`: 10 facets
- `safety`: 8 facets
- `health_and_lifestyle`: 7 facets
- `linguistic_quality`: 3 facets

## 4. Tech Stack

- **Backend:** Flask
- **Schema validation:** Pydantic v2
- **LLM inference:** Hugging Face `transformers`
- **Model:** `Qwen/Qwen2.5-0.5B-Instruct`
- **Database:** SQLite by default through SQLAlchemy
- **Config:** `pydantic-settings` with `ACE_` environment variables
- **Containerization:** Docker and Docker Compose
- **Data format:** JSON/YAML facet registry, JSON API requests

## 5. Main Features

- Dynamic facet registry loaded from JSON/YAML
- 399 generated facets from assignment CSV
- Five-point scale: `1 = low evidence`, `5 = high evidence`
- Facet batching to support large registries
- Qwen-based per-turn evaluation
- Strict JSON response parsing from the model
- Fallback behavior when model output is malformed
- Per-facet score, confidence, reasoning summary, evaluator metadata
- Weighted aggregation at turn, category, and conversation level
- Flask REST API
- Simple dashboard UI
- SQLite persistence
- Docker support
- Structured trace logs for evaluation batches

## 6. Important Files And Responsibilities

| File | Purpose |
| --- | --- |
| `app/__main__.py` | Starts the Flask app with `python -m app` |
| `app/core/config.py` | Loads settings from `.env` and `ACE_` variables |
| `app/core/factory.py` | Creates the Flask app and registers API/UI blueprints |
| `app/core/container.py` | Wires registry, evaluator, batching, storage, aggregation, and pipeline |
| `app/api/routes.py` | Defines `/health`, `/facets`, `/evaluate`, and `/conversation/<id>` |
| `app/models/schemas.py` | Pydantic request/response/domain schemas |
| `app/facets/registry.py` | Loads and filters facet definitions |
| `app/services/batch_engine.py` | Splits facets into manageable batches |
| `app/services/evaluation_service.py` | Calls evaluator batch by batch and calibrates confidence |
| `app/evaluators/transformers_evaluator.py` | Qwen/transformers adapter, prompt building, JSON parsing |
| `app/services/aggregation_service.py` | Computes normalized weighted scores and category metrics |
| `app/services/sqlalchemy_storage.py` | Persists conversations, evaluations, facets, and metrics |
| `app/models/orm.py` | SQLAlchemy database tables |
| `configs/facets.assignment.json` | Main 399-facet registry |
| `documentation/api_examples.md` | Example API calls |
| `documentation/architecture.md` | Architecture and scaling notes |

## 7. Runtime Flow

```text
HTTP request
  -> Flask route `/evaluate`
  -> Pydantic `EvaluateRequest` validation
  -> `FacetRegistry.filter()`
  -> `ConversationEvaluationPipeline.run()`
  -> For each turn:
       -> `FacetBatchingEngine.batches()`
       -> `TransformersEvaluator.evaluate_turn()`
       -> Qwen generates strict JSON
       -> parse, clamp, and convert to `FacetEvaluation`
       -> confidence calibration
       -> weighted turn aggregation
  -> category and conversation metrics
  -> SQLAlchemy persistence
  -> JSON response
```

## 8. API Endpoints

### `GET /health`

Checks service status and returns evaluator backend and enabled facet count.

### `GET /facets`

Lists configured facets. Supports:

```text
?category=safety
?include_disabled=true
```

### `POST /evaluate`

Evaluates a conversation. Example:

```bash
curl -X POST http://localhost:8000/evaluate \
  -H "Content-Type: application/json" \
  -d @documentation/example_request.json
```

The response includes:

- `turns[].facet_scores[]`
- `score`
- `confidence`
- `reasoning_summary`
- `aggregate_score`
- `metrics.overall_score`
- `metrics.category_scores`

### `GET /conversation/<conversation_id>`

Fetches a stored conversation and latest evaluation result.

## 9. Configuration

The app reads `.env` values using the `ACE_` prefix.

```bash
ACE_EVALUATOR_BACKEND=qwen
ACE_QWEN_MODEL_NAME=Qwen/Qwen2.5-0.5B-Instruct
ACE_STORAGE_BACKEND=sqlalchemy
ACE_DATABASE_URL=sqlite:///data/evaluations.db
ACE_FACET_BATCH_SIZE=5
ACE_FACET_CONFIG_PATH=configs/facets.assignment.json
ACE_TRACE_ENABLED=true
```

Run locally:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app
```

Run with Docker:

```bash
docker compose up --build
```

Open:

```text
http://localhost:8000
```

## 10. Database Design

The app uses SQLAlchemy and SQLite by default. Main tables:

- `conversations`: original conversation payload
- `turns`: individual conversation turns
- `facets`: synced facet definitions
- `evaluation_results`: full evaluation response payload
- `facet_evaluations`: one row per evaluated turn/facet pair
- `metrics`: overall and category-level metrics

SQLite path:

```text
data/evaluations.db
```

## 11. Scoring And Aggregation

Each facet has:

- `facet_id`
- `category`
- `description`
- `score_scale`
- `evaluation_strategy`
- `weight`
- `tags`
- metadata such as source CSV row and rubric question

Raw scores use the five-point scale. Aggregation normalizes each score to `0.0 - 1.0`:

```text
normalized = (score - min_score) / (max_score - min_score)
```

Then the app computes weighted averages:

- Turn aggregate score
- Turn aggregate confidence
- Category scores
- Overall conversation score
- Overall confidence

## 12. Why The Design Scales

The project scales because facets are data, not code. Adding new evaluation dimensions means updating the registry, not rewriting the evaluation pipeline.

Important scalability choices:

- Batch engine prevents one huge prompt.
- Evaluator interface allows swapping Qwen for another model or hosted inference.
- Storage boundary allows SQLite locally and stronger databases later.
- Categories and strategies allow future sharding by evaluation type.
- Trace spans expose batch size, turn id, evaluator, and timing.

For production scale, I would add:

- Async job queue with Celery/RQ/Kafka
- Postgres instead of SQLite
- vLLM or TGI model serving
- Registry versioning
- Prompt templates per facet category
- Better model output validation and retries
- Observability with OpenTelemetry
- Evaluation calibration dataset

## 13. Key Design Decisions

### Why Flask?

Flask is lightweight and enough for an assignment/demo service. The code separates routes from services, so moving to FastAPI later would not require rewriting the core pipeline.

### Why Pydantic?

Pydantic gives strict request/response validation and keeps the API schema explicit.

### Why a facet registry?

The project needs hundreds of evaluation dimensions. A registry makes facets configurable, filterable, and extensible.

### Why batching?

Sending all 399 facets in one prompt would be too large and unreliable. Batching controls prompt size and gives a path to scale to thousands of facets.

### Why SQLAlchemy?

It provides a clean persistence layer and makes switching from SQLite to Postgres easier.

### Why Qwen?

Qwen is an open-weight model suitable for local/demo inference and fits the assignment requirement better than relying on a proprietary hosted API.

## 14. Strengths To Mention In Interview

- Schema-first API design
- Clear service boundaries
- Dynamic, data-driven facet evaluation
- Batched LLM inference
- Robust parsing fallback for imperfect model output
- Weighted scoring and category-level metrics
- Local reproducibility with Docker
- Database persistence for later analysis
- Extensible evaluator interface

## 15. Known Limitations

- Current implementation is synchronous, so large evaluations can block the request.
- SQLite is fine for demos but not ideal for high-volume production traffic.
- Local Qwen inference can be slow, especially on CPU.
- Model output quality depends on prompt compliance.
- No source test files are currently present in the checkout, although pytest cache files indicate tests existed previously.
- README still has a small stale path reference to `docs/`; the current folder is `documentation/`.

## 16. Interview Q&A Cheat Sheet

### Q: What does your project do?

It evaluates conversation turns across 399 configurable facets like safety, emotion, pragmatics, personality, and linguistic quality. It uses a Qwen model to score each turn, returns confidence and reasoning, and aggregates results into turn, category, and overall metrics.

### Q: What was the main architectural idea?

The main idea was to make evaluation criteria data-driven. Facets live in a JSON registry, and the pipeline loads, filters, batches, evaluates, and aggregates them without hardcoding specific criteria.

### Q: How does the evaluation pipeline work?

The API validates a conversation, selects facets from the registry, splits them into batches, sends each turn and facet batch to Qwen, parses strict JSON output, calibrates confidence, computes weighted normalized scores, stores the result, and returns a JSON response.

### Q: How did you handle 399 facets?

I used batching. The `FacetBatchingEngine` splits facets into smaller groups, controlled by `ACE_FACET_BATCH_SIZE`, so the system avoids huge prompts and can scale toward larger registries.

### Q: How are scores calculated?

Each facet gets a raw score from 1 to 5. The aggregation service normalizes scores to 0 to 1, applies facet weights, and computes averages for each turn, category, and conversation.

### Q: How do you handle malformed LLM output?

The transformer evaluator asks for strict JSON, extracts JSON from the model response, validates facet ids, clamps scores and confidence into valid ranges, and returns a low-confidence fallback when a facet result is missing.

### Q: How would you make it production ready?

I would add async workers, Postgres, model serving through vLLM/TGI, registry versioning, stronger retry logic, observability, authentication, rate limits, and a calibration dataset for measuring evaluator reliability.

### Q: Why did you choose this design?

Because the problem is about scalable evaluation. If every facet were hardcoded, the app would become difficult to maintain. A registry-plus-pipeline design lets the number of facets grow while keeping the code stable.

### Q: What are the main tradeoffs?

The current app is simple and reproducible, but synchronous local inference can be slow. SQLite is convenient for demos but should be replaced with Postgres for production. The LLM is flexible, but output validation and calibration are important.

### Q: What part are you most proud of?

The clean separation between registry, batching, evaluator, aggregation, and storage. It makes the project easy to explain, test, and extend.

## 17. Copy-Paste Prompt For ChatGPT During Interview Prep

Use this prompt with ChatGPT:

```text
I am interviewing for an AI/ML Engineer role. Use the project overview below to answer interview questions quickly and clearly. Keep answers concise, practical, and in first person as if I built the project. Focus on architecture, design decisions, scalability, tradeoffs, and production improvements.

[Paste this markdown file here]
```

