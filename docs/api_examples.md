# API Examples

## Health

```bash
curl http://localhost:8000/health
```

## List Facets

```bash
curl http://localhost:8000/facets
curl "http://localhost:8000/facets?category=safety"
```

## Evaluate

```bash
curl -X POST http://localhost:8000/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "conversation": {
      "conversation_id": "demo-001",
      "turns": [
        { "role": "user", "text": "I feel overwhelmed and need a study plan." },
        { "role": "assistant", "text": "I understand. Start with one topic today, then review model evaluation tomorrow." }
      ],
      "metadata": { "source": "manual" }
    },
    "categories": ["emotion", "pragmatics"],
    "batch_size": 10
  }'
```

The response contains `turns[].facet_scores[]` with `score`, `confidence`, and `reasoning_summary`, plus weighted `metrics`.
