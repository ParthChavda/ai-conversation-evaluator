from app import create_app


def test_health_endpoint():
    app = create_app()
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_evaluate_endpoint_returns_scores():
    app = create_app()
    client = app.test_client()
    payload = {
        "conversation": {
            "conversation_id": "test-convo",
            "turns": [
                {"role": "user", "text": "I feel sad and need help making a plan."},
                {"role": "assistant", "text": "I understand and can help with a simple next step."},
            ],
        },
        "categories": ["emotion", "safety"],
        "batch_size": 2,
    }

    response = client.post("/evaluate", json=payload)
    body = response.get_json()

    assert response.status_code == 200
    assert body["conversation_id"] == "test-convo"
    assert body["metrics"]["total_turns"] == 2
    assert body["metrics"]["batches_executed"] == 4
    assert body["turns"][0]["facet_scores"][0]["confidence"] >= 0


def test_get_conversation_after_evaluation():
    app = create_app()
    client = app.test_client()
    payload = {
        "conversation": {
            "conversation_id": "stored-convo",
            "turns": [{"role": "user", "text": "Hello, can you help me?"}],
        }
    }

    client.post("/evaluate", json=payload)
    response = client.get("/conversation/stored-convo")

    assert response.status_code == 200
    assert response.get_json()["latest_evaluation"]["conversation_id"] == "stored-convo"
