# AI Conversation Evaluator

Production-oriented Flask benchmark framework for evaluating every conversation turn across modular facets covering linguistic quality, pragmatics, safety, emotion, and conversational intelligence.

The project is schema-first: no CSV is required. Facets load dynamically from JSON/YAML, conversations are accepted through APIs, and the mock evaluator makes the full pipeline runnable without proprietary APIs or hosted models.

## Highlights

- Dynamic facet registry with score scales, strategy metadata, weights, tags, and enabled flags.
- Batch evaluation engine designed for 300 facets today and 5000+ facets without redesign.
- Plugin-style evaluator interface for Qwen, Llama, Mixtral-compatible models, and deterministic mock inference.
- Per-turn facet scores with confidence values and reasoning summaries.
- Weighted aggregation at turn, category, and conversation levels.
- Flask API, dashboard UI, Docker support, synthetic dataset, benchmark script, structured trace logs.
- SQLite persistence by default, Postgres-ready database URL config.
- Redis/Celery-ready queue boundary, model cache, and experiment tracking placeholders.

## Project Structure

```text
app/
  api/                 Flask API routes
  confidence/          confidence calibration hooks
  core/                config, app factory, dependency container
  evaluators/          evaluator interface and model adapters
  facets/              dynamic facet registry
  models/              Pydantic schemas and DB-ready dataclasses
  pipelines/           conversation evaluation orchestration
  preprocessing/       normalization extension points
  services/            batching, aggregation, storage, queue, cache
  ui/                  minimal dashboard
configs/               facet registry examples
data/                  synthetic conversation dataset
docker/                worker container placeholder
docs/                  architecture and API examples
scripts/               data and benchmark utilities
tests/                 pytest suite
```

SQLite data is stored at `data/evaluations.db` by default and ignored by git.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app
```

Open `http://localhost:8000` for the dashboard.

## API

```bash
curl http://localhost:8000/health
curl http://localhost:8000/facets
curl -X POST http://localhost:8000/evaluate \
  -H "Content-Type: application/json" \
  -d @docs/example_request.json
```

See [docs/api_examples.md](docs/api_examples.md) for inline examples.

## Docker

```bash
docker compose up --build
```

The app runs on `http://localhost:8000` with Redis available for future async workers.

## Configuration

Environment variables use the `ACE_` prefix.

```bash
ACE_EVALUATOR_BACKEND=mock
ACE_STORAGE_BACKEND=sqlalchemy
ACE_DATABASE_URL=sqlite:///data/evaluations.db
POSTGRES_DB=ai_conversation_evaluator
POSTGRES_HOST=localhost
POSTGRES_PASSWORD=postgres
POSTGRES_PORT=5432
POSTGRES_USER=postgres
ACE_FACET_BATCH_SIZE=25
ACE_FACET_CONFIG_PATH=configs/facets.example.json
ACE_TRACE_ENABLED=true
```

Supported evaluator backend names are `mock`, `qwen`, `llama`, and `mixtral`. The real model path uses local `transformers` generation and strict JSON parsing. `mock` remains the default because it is fast and does not download model weights.

Example local Qwen run:

```bash
cp .env.example .env
ACE_EVALUATOR_BACKEND=qwen \
ACE_QWEN_MODEL_NAME=Qwen/Qwen2.5-1.5B-Instruct \
ACE_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/ai_conversation_evaluator \
python -m app
```

The first run downloads model weights from Hugging Face and may be slow. For laptop demos, keep batches small with `ACE_FACET_BATCH_SIZE=3`.

## Postgres And pgAdmin

The recommended local database name is:

```text
ai_conversation_evaluator
```

Default local credentials used by `docker-compose.yml` and `.env.example`:

```text
host: localhost
port: 5432
database: ai_conversation_evaluator
user: postgres
password: postgres
SQLAlchemy URL: postgresql+psycopg://postgres:postgres@localhost:5432/ai_conversation_evaluator
```

You can either set `ACE_DATABASE_URL` directly or provide the `POSTGRES_*` variables above. If both are present, `ACE_DATABASE_URL` wins.

Start Postgres and pgAdmin:

```bash
docker compose up postgres pgadmin
```

Open pgAdmin at `http://localhost:5050`.

pgAdmin login:

```text
email: admin@example.com
password: admin
```

Register the Postgres server in pgAdmin with:

```text
host: postgres
port: 5432
database: ai_conversation_evaluator
username: postgres
password: postgres
```

When running the Flask app directly from your host machine instead of inside Docker, use `localhost` in `ACE_DATABASE_URL`. When running inside Docker Compose, use `postgres`.

## Scalability Notes

The framework scales by treating facets as data, not code. The pipeline never assumes a fixed facet count; it filters registry records, chunks them, evaluates each batch, and aggregates normalized scores. For 5000+ facets, run workers by category or strategy, persist jobs in Redis/Kafka, and store evaluations in Postgres or a columnar benchmark store.

## Testing And Benchmarking

```bash
pytest
python -m scripts.benchmark
```

## Future Improvements

- Add SQLAlchemy repositories and migrations for durable storage.
- Implement Celery tasks for async `/evaluate` submissions.
- Add OpenTelemetry exporters for traces and latency metrics.
- Add evaluator-specific prompt templates and constrained JSON decoding.
- Add calibration datasets and reliability curves for confidence scoring.
- Add facet authoring UI and registry versioning.
