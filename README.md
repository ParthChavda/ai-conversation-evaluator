# AI Conversation Evaluator

Flask app for scoring conversation turns across many evaluation facets.

This project was built for the Ocean Across AI/ML Engineer assignment. It takes a facet CSV, converts it into a JSON registry, accepts conversations through an API, scores every turn with an open-weight Qwen model, and returns scores with confidence values.

## What It Includes

- Flask API and simple dashboard UI
- Facet preprocessing from `data/facets_assignment.csv`
- 399 generated facets in `configs/facets.assignment.json`
- Five-point score scale: `1` to `5`
- Batched facet evaluation, so the design can scale beyond the current facet count
- Qwen open-weight evaluator: `Qwen/Qwen2.5-0.5B-Instruct`
- Per-turn facet scores, confidence, and short reasoning
- SQLite storage for local runs
- Docker setup
- Submission zip with 50 scored conversations

## Project Structure

```text
app/
  api/             Flask API routes
  core/            app setup and configuration
  evaluators/      Qwen evaluator
  facets/          facet registry
  models/          request and response schemas
  pipelines/       evaluation flow
  services/        batching, scoring, aggregation, storage
  ui/              dashboard
configs/           generated facet registry
data/              source CSV and synthetic conversations
docs/              API examples and architecture notes
```

## Run Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app
```

Open:

```text
http://localhost:8000
```

Health check:

```bash
curl http://localhost:8000/health
```

Evaluate one example:

```bash
curl -X POST http://localhost:8000/evaluate \
  -H "Content-Type: application/json" \
  -d @docs/example_request.json
```

## Docker

```bash
docker compose up --build
```

The app runs on:

```text
http://localhost:8000
```

## Configuration

The app reads environment variables with the `ACE_` prefix.

```bash
ACE_EVALUATOR_BACKEND=qwen
ACE_QWEN_MODEL_NAME=Qwen/Qwen2.5-0.5B-Instruct
ACE_STORAGE_BACKEND=sqlalchemy
ACE_DATABASE_URL=sqlite:///data/evaluations.db
ACE_FACET_BATCH_SIZE=5
ACE_FACET_CONFIG_PATH=configs/facets.assignment.json
ACE_TRACE_ENABLED=true
```

The first Qwen run can be slow because the model has to load or download.

## Submission Zip

The generated assignment zip is:

```text
conversation_scores_submission.zip
```

It contains 50 synthetic conversations and scored outputs.

The zip uses a representative subset of facets for sample scoring. The app itself supports the full generated facet registry.

## Notes

- The benchmark is not a one-shot prompt. Facets are loaded as data, batched, evaluated, and aggregated.
- The evaluator uses an open-weight model under the assignment limit.
- The code is structured so more facets can be added through the registry without changing the main pipeline.
